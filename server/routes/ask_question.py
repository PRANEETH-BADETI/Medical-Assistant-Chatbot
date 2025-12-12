# server/routes/ask_question.py

from fastapi import APIRouter, Form, Depends
from fastapi.responses import StreamingResponse
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers.merger_retriever import MergerRetriever
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from modules.llm import get_llm_chain
from logger import logger
from config import pc, embed_model, PINECONE_INDEX_NAME, llm, PINECONE_API_KEY, GLOBAL_KB_NAMESPACE

from sqlalchemy.orm import Session
from database import get_db
import crud.message as message_crud
from schemas.message import MessageCreate
from models.message import MessageRole

from utils.auth_deps import get_current_user
from models.user import User
import asyncio


router = APIRouter(prefix="/ask", tags=["ask"])


async def stream_generator(chain, question: str, db: Session, user: User):
    """
    Generator function to stream the response and save it to the DB.
    """

    # 1. Save the user's message to the DB
    try:
        message_crud.create_message(
            db=db,
            message=MessageCreate(content=question, role=MessageRole.USER),
            user_id=user.id
        )
    except Exception as e:
        logger.error(f"Failed to save user message: {e}")
        # Don't stop the stream, just log the error

    full_response = ""
    try:
        # --- FIX IS HERE ---
        # Change "question" to "input" in the dictionary below:
        async for chunk in chain.astream({"input": question}):

            # LCEL yields a dict. We want the "answer" field.
            if "answer" in chunk:
                token = chunk["answer"]
                full_response += token
                yield token

    except Exception as e:
        logger.error(f"Error during chain streaming: {e}")
        yield f"Error: {str(e)}"


    finally:

        # 3. Save Assistant Response

        if full_response:

            try:

                message_crud.create_message(

                    db=db,

                    message=MessageCreate(content=full_response, role=MessageRole.ASSISTANT),

                    user_id=user.id

                )

            except Exception as e:

                logger.error(f"Failed to save AI response: {e}")


@router.post("/")
async def ask_question(
        question: str = Form(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Asks a question to the LLM and streams the response.
    """
    try:
        logger.info(f"User query from {current_user.email}: {question}")

        # --- Multi-Tenant Retriever Logic ---
        vectorstore = PineconeVectorStore(
            index_name=PINECONE_INDEX_NAME,
            embedding=embed_model,
            pinecone_api_key=PINECONE_API_KEY
        )
        user_namespace = f"user_{current_user.id}"
        user_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 2, "namespace": user_namespace}
        )
        global_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 2, "namespace": GLOBAL_KB_NAMESPACE}
        )
        retriever = MergerRetriever(retrievers=[user_retriever, global_retriever])
        # --- End Retriever Logic ---

        # Get the LLM chain
        # NOTE: We pass the *synchronous* llm object,
        # but the RetrievalQA.ainvoke method will run it asynchronously.
        chain = get_llm_chain(retriever, llm)

        # Return the streaming response
        return StreamingResponse(
            stream_generator(chain, question, db, current_user),
            media_type="text/plain"
        )

    except Exception as e:
        logger.exception(f"Error on asking question: {str(e)}")
        # This will be caught by the frontend as a non-streaming error
        return StreamingResponse(
            iter(["I'm sorry, a server error occurred. Please try again."]),
            media_type="text/plain",
            status_code=500
        )