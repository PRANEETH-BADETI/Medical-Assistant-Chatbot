from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from langchain_pinecone import PineconeVectorStore
from modules.llm import get_llm_chain
from modules.query_handlers import query_chain
from logger import logger
from config import pc, embed_model, PINECONE_INDEX_NAME, llm, PINECONE_API_KEY

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("/")
async def ask_question(question: str = Form(...)):
    try:
        logger.info(f"User query: {question}")

        # Use PineconeVectorStore as a retriever
        vectorstore = PineconeVectorStore(
            index_name=PINECONE_INDEX_NAME,
            embedding=embed_model,
            pinecone_api_key=PINECONE_API_KEY
        )

        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Get the LLM chain with the retriever and pre-initialized LLM
        chain = get_llm_chain(retriever, llm)

        result = query_chain(chain, question)

        logger.info("Query successful")
        return result

    except Exception as e:
        logger.exception(f"Error on asking question: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "An unexpected error occurred."})