from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers.merger_retriever import MergerRetriever
from modules.llm import get_llm_chain
from modules.query_handlers import query_chain
from logger import logger
from config import pc, embed_model, PINECONE_INDEX_NAME, llm, PINECONE_API_KEY, GLOBAL_KB_NAMESPACE
from utils.auth_deps import get_current_user
from models.user import User

router = APIRouter(prefix="/ask", tags=["ask"])

@router.post("/")
async def ask_question(question: str = Form(...),
    current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"User query from {current_user.email}: {question}")

        # Use PineconeVectorStore as a retriever
        vectorstore = PineconeVectorStore(
            index_name=PINECONE_INDEX_NAME,
            embedding=embed_model,
            pinecone_api_key=PINECONE_API_KEY
        )

        # 2. Create a retriever for the user's private namespace
        user_namespace = f"user_{current_user.id}"
        user_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 2, "namespace": user_namespace}
        )
        logger.debug(f"Searching in user namespace: {user_namespace}")

        # 3. Create a retriever for the global admin namespace
        global_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 2, "namespace": GLOBAL_KB_NAMESPACE}
        )
        logger.debug(f"Searching in global namespace: {GLOBAL_KB_NAMESPACE}")

        # 4. Create the MergerRetriever (aka "Ensemble Retriever")
        # This will run both retrievers and combine the results.
        retriever = MergerRetriever(retrievers=[user_retriever, global_retriever])

        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Get the LLM chain with the retriever and pre-initialized LLM
        chain = get_llm_chain(retriever, llm)

        result = query_chain(chain, question)

        logger.info("Query successful")
        return result

    except Exception as e:
        logger.exception(f"Error on asking question: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "An unexpected error occurred."})