"""
QUERY_ENGINE.PY — The Brain of Doubt Buddy
=============================================
This module:
1. Loads the vector database (teacher's indexed content)
2. Retrieves relevant chunks for a student's question
3. Sends them to Claude with a strict prompt
4. Returns a grounded answer + optional quiz
"""

import os
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic
import chromadb

CHROMA_DIR = "chroma_db"

# ── The system prompt that keeps Claude grounded in teacher's content ──
SYSTEM_PROMPT = """You are "KnowledgeHub Buddy", an AI teaching assistant for an English class.

CRITICAL RULES:
1. You must ONLY answer based on the teaching material provided in the context below.
2. If the student's question is NOT covered in the provided context, say:
   "This topic isn't covered in our class materials yet. Please ask your teacher about it in the next class!"
3. Do NOT use any knowledge from the internet or your training data.
4. Always reference which lesson or topic your answer comes from.
5. Use simple, encouraging language — these are students learning English.
6. Give examples from the teaching material whenever possible.
7. If a student seems confused, break down the concept step by step.

RESPONSE FORMAT:
- Start with a clear, friendly answer to their question
- Include relevant examples from the teaching material
- Reference the lesson/topic (e.g., "As covered in Lesson 1: Present Tenses...")
- End with a section called "Quick Check" containing 2-3 multiple choice questions 
  to help the student verify they understood the concept. Format each question like:

  **Quick Check — Did you get it?**
  
  **Q1:** [Question text]
  - A) [option]
  - B) [option]
  - C) [option]
  - **Answer:** [correct letter and brief explanation]

Keep the quiz questions focused on the specific doubt the student asked about.
"""


def get_query_engine():
    """
    Load the knowledge base and create a query engine.
    Returns a configured query engine ready to answer questions.
    """

    # ── Check API key ──
    #api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    import streamlit as st
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set! Please set it:\n"
            "  Windows: set ANTHROPIC_API_KEY=your-key-here\n"
            "  Mac/Linux: export ANTHROPIC_API_KEY=your-key-here"
        )

    # ── Check knowledge base exists ──
    if not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError(
            "Knowledge base not found! Please run 'python ingest.py' first."
        )

    # ── Setup embedding model (same one used during ingestion) ──
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    Settings.embed_model = embed_model

    # ── Setup Claude as the LLM ──
    llm = Anthropic(
        model="claude-sonnet-4-20250514",
        api_key=api_key,
        temperature=0.3,       # Lower = more focused, less creative
        max_tokens=1500,       # Enough for answer + quiz
        system_prompt=SYSTEM_PROMPT,
    )
    Settings.llm = llm

    # ── Load the vector database ──
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    chroma_collection = chroma_client.get_collection("teacher_knowledge")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # ── Create index from existing store ──
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
    )

    # ── Create query engine ──
    # similarity_top_k=3 means retrieve top 3 most relevant chunks
    query_engine = index.as_query_engine(
        similarity_top_k=3,
        response_mode="compact",   # Combines chunks into one coherent answer
    )

    return query_engine


def ask_doubt(query_engine, question: str) -> str:
    """
    Send a student's question to the query engine.
    Returns the AI's response (answer + quiz).
    """
    response = query_engine.query(question)
    return str(response)


# ── For testing from command line ──
if __name__ == "__main__":
    print("Loading knowledge base...")
    engine = get_query_engine()
    print("Ready! Type your questions (or 'quit' to exit):\n")

    while True:
        question = input("🙋 Your question: ")
        if question.lower() in ("quit", "exit", "q"):
            break
        print("\n🤖 Doubt Buddy:")
        answer = ask_doubt(engine, question)
        print(answer)
        print("\n" + "-" * 50 + "\n")
