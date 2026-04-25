"""
INGEST.PY — Knowledge Base Builder
====================================
This script reads all files in the teacher_content/ folder,
breaks them into chunks, creates embeddings, and stores them
in a local ChromaDB vector database.

Run this whenever you add new teaching materials:
    python ingest.py
"""

import os
import sys
import shutil
from pathlib import Path

# ── Setup paths ──────────────────────────────────────────────
CONTENT_DIR = "teacher_content"
SAMPLE_DIR = "sample_content"
CHROMA_DIR = "chroma_db"

def check_content_folder():
    """Make sure teacher_content folder exists and has files."""
    os.makedirs(CONTENT_DIR, exist_ok=True)

    # Check if there are any files in teacher_content
    content_files = list(Path(CONTENT_DIR).glob("*"))
    content_files = [f for f in content_files if f.is_file()]

    if len(content_files) == 0:
        print("\n📂 No files found in 'teacher_content/' folder.")
        print("   Copying sample content for you to test with...\n")

        # Copy sample content
        if os.path.exists(SAMPLE_DIR):
            for f in Path(SAMPLE_DIR).glob("*"):
                if f.is_file():
                    shutil.copy(f, CONTENT_DIR)
                    print(f"   ✓ Copied: {f.name}")
            print()
        else:
            print("   ❌ No sample content found either.")
            print("   Please add PDF, DOCX, or TXT files to 'teacher_content/' folder.")
            sys.exit(1)


def load_documents():
    """Load all documents from teacher_content folder."""
    from llama_index.core import SimpleDirectoryReader

    print("📖 Reading teacher's content files...")

    # SimpleDirectoryReader handles PDF, DOCX, TXT automatically
    reader = SimpleDirectoryReader(
        input_dir=CONTENT_DIR,
        recursive=True,
        filename_as_id=True,
        required_exts=[".pdf", ".docx", ".txt", ".md"],
    )

    documents = reader.load_data()
    print(f"   ✓ Loaded {len(documents)} document chunks from {CONTENT_DIR}/\n")

    # Show what was loaded
    seen_files = set()
    for doc in documents:
        source = doc.metadata.get("file_name", "unknown")
        if source not in seen_files:
            seen_files.add(source)
            print(f"   📄 {source}")

    print()
    return documents


def create_index(documents):
    """Create vector embeddings and store in ChromaDB."""
    from llama_index.core import VectorStoreIndex, StorageContext, Settings
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    import chromadb

    # ── Use free local embeddings (no API cost!) ──
    print("🧠 Setting up embedding model (first time takes 2-3 min to download)...")
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    Settings.embed_model = embed_model
    # We don't need an LLM for indexing, only for querying
    Settings.llm = None

    # ── Chunk the documents ──
    print("✂️  Splitting content into searchable chunks...")
    splitter = SentenceSplitter(
        chunk_size=512,      # ~512 tokens per chunk
        chunk_overlap=50,    # 50 token overlap for context continuity
    )

    # ── Setup ChromaDB (local, free) ──
    print("💾 Creating vector database...")

    # Clear old database if it exists
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)

    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    chroma_collection = chroma_client.get_or_create_collection("teacher_knowledge")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # ── Build the index ──
    print("📊 Creating embeddings and building index...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        transformations=[splitter],
        show_progress=True,
    )

    print(f"\n✅ Knowledge base created successfully!")
    print(f"   Stored in: {CHROMA_DIR}/")
    print(f"   Total chunks indexed: {len(chroma_collection.get()['ids'])}")

    return index


def main():
    print("=" * 60)
    print("  🌳 KnowledgeHub Buddy — Knowledge Base Builder")
    print("=" * 60)
    print()

    # Step 1: Check content
    check_content_folder()

    # Step 2: Load documents
    documents = load_documents()

    if len(documents) == 0:
        print("❌ No documents found. Please add files to 'teacher_content/' folder.")
        sys.exit(1)

    # Step 3: Create index
    create_index(documents)

    print()
    print("🎉 All done! You can now run the app:")
    print("   streamlit run app.py")
    print()


if __name__ == "__main__":
    main()
