# 🩺 Medical Assistant Chatbot

An AI-powered assistant designed to provide medical information and
insights from custom, uploaded documents.

## ✨ Features

-   **Retrieval-Augmented Generation (RAG):** Answers user questions by
    retrieving relevant information from a custom document knowledge
    base.
-   **Multi-modal Document Support:** Capable of processing and
    understanding both PDFs and images (PNG, JPG, JPEG).
-   **Intelligent Vision Model:** Leverages Google's Gemini Vision model
    to read and interpret text from uploaded images like lab reports and
    medical charts.
-   **Fast & Responsive API:** Built with FastAPI and powered by the
    Groq API's Llama-3.3-70B model for high-speed, accurate responses.
-   **Scalable Vector Database:** Uses Pinecone to efficiently store and
    retrieve document embeddings, ensuring high performance even with a
    large corpus of data.
-   **Intuitive User Interface:** A clean and easy-to-use Streamlit
    frontend for seamless file uploads and conversational interaction.

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

-   Python 3.9+
-   A `.env` file with the necessary API keys (refer to the
    Configuration section below).
-   A virtual environment is highly recommended.

### Installation

Clone the repository:

``` bash
git clone https://github.com/your-username/medical-assistant-chatbot.git
cd medical-assistant-chatbot/server
```

Create a virtual environment and activate it:

``` bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
```

Install the dependencies:

``` bash
pip install -r requirements.txt
```

### Configuration

Create a file named `.env` in the server directory with your API keys:

``` env
GOOGLE_API_KEY="your_google_api_key"
PINECONE_API_KEY="your_pinecone_api_key"
GROQ_API_KEY="your_groq_api_key"
PINECONE_INDEX_NAME="medicalindex"
```

### Usage

Start the backend API:

``` bash
uvicorn main:app --port 8000 --reload
```

The API will be accessible at <http://127.0.0.1:8000>.

In a new terminal, start the Streamlit client:

``` bash
cd ../client  # Go back to the client directory
streamlit run app.py
```

The UI will open in your browser, where you can upload documents and
start chatting.

## 📁 Project Structure

    medical-assistant-chatbot/
    ├── server/
    │   ├── .env
    │   ├── main.py
    │   ├── routes/
    │   │   ├── ask_question.py
    │   │   ├── upload_pdfs.py
    │   │   └── ...
    │   ├── modules/
    │   │   ├── llm.py
    │   │   ├── load_vectorstore.py
    │   │   └── ...
    │   ├── requirements.txt
    │   └── ...
    ├── client/
    │   ├── .streamlit/
    │   │   └── secrets.toml
    │   ├── app.py
    │   ├── requirements.txt
    │   └── ...
    └── README.md

