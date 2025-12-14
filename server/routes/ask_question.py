import json
from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from logger import logger
from config import pc, embed_model, PINECONE_INDEX_NAME, llm, PINECONE_API_KEY, GLOBAL_KB_NAMESPACE
from sqlalchemy.orm import Session
from database import get_db
import crud.message as message_crud
import crud.chat as chat_crud
from schemas.message import MessageCreate
from models.message import MessageRole
from utils.auth_deps import get_current_user
from models.user import User

router = APIRouter(prefix="/ask", tags=["ask"])


async def stream_generator(question, session_id, db, user, vectorstore, session_namespace):
    # 1. Save User Message
    message_crud.create_message(
        db, MessageCreate(content=question, role=MessageRole.USER), user.id, session_id
    )

    # 2. Auto-Title Check
    msgs = message_crud.get_messages_by_session(db, session_id, user.id)
    if len(msgs) <= 2:
        try:
            title_prompt = ChatPromptTemplate.from_template(
                "Summarize this question into a short 3-5 word title: {question}"
            )
            title_chain = title_prompt | llm | StrOutputParser()
            new_title = title_chain.invoke({"question": question}).strip('"')
            chat_crud.update_session_title(db, session_id, new_title, user.id)
        except Exception:
            pass

    full_response = ""
    source_metadata = []

    try:
        # 3. HYBRID RETRIEVAL (Session + Global)

        # A. Search Private Session
        docs_session = vectorstore.similarity_search_with_score(
            question, k=3, namespace=session_namespace
        )
        # Tag them as Private
        for doc, _ in docs_session:
            doc.metadata["source_type"] = "Private"

        # B. Search Global Knowledge Base
        docs_global = vectorstore.similarity_search_with_score(
            question, k=3, namespace=GLOBAL_KB_NAMESPACE
        )
        # Tag them as Global
        for doc, _ in docs_global:
            doc.metadata["source_type"] = "Global"

        # C. Combine & Sort
        all_docs = docs_session + docs_global
        all_docs.sort(key=lambda x: x[1], reverse=True)
        final_docs = all_docs[:4]

        # Prepare Context
        context_text = "\n\n".join([d.page_content for d, _ in final_docs])

        # Prepare Metadata (Including the new "type" field)
        unique_sources = {}
        for doc, score in final_docs:
            src = doc.metadata.get("source", "Unknown")
            if src not in unique_sources:
                unique_sources[src] = {
                    "source": src,
                    "score": round(score, 4),
                    "type": doc.metadata.get("source_type", "Private")  # <--- Sending this to UI
                }
        source_metadata = list(unique_sources.values())

        # 4. Generate Answer
        system_prompt = """You are MediBot. Answer based ONLY on the context.
        Context: {context}
        Question: {question}"""

        prompt = ChatPromptTemplate.from_template(system_prompt)
        chain = prompt | llm | StrOutputParser()

        async for chunk in chain.astream({"context": context_text, "question": question}):
            full_response += chunk
            yield chunk

        # 5. Append Sources
        if source_metadata:
            yield f"|||SOURCES|||{json.dumps(source_metadata)}"

    except Exception as e:
        yield f"Error: {e}"

    finally:
        if full_response:
            message_crud.create_message(
                db, MessageCreate(content=full_response, role=MessageRole.ASSISTANT),
                user.id, session_id
            )


@router.post("/{session_id}")
async def ask_question(
        session_id: int,
        question: str = Form(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    session = chat_crud.get_session(db, session_id, current_user.id)
    if not session: raise HTTPException(404, "Session not found")

    vectorstore = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME, embedding=embed_model, pinecone_api_key=PINECONE_API_KEY
    )

    # Pass the private namespace. The generator will ALSO check global.
    session_namespace = f"session_{session_id}"

    return StreamingResponse(
        stream_generator(question, session_id, db, current_user, vectorstore, session_namespace),
        media_type="text/plain"
    )