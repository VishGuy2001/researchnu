#!/bin/bash
# ResearchNu — start API + frontend

# Pre-load BERT model so first user request isn't slow
echo "Pre-loading embedding model..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" 

# Start FastAPI backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit frontend (foreground — keeps container alive)
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true