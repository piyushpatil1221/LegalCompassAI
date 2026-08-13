# LegalCompass AI

**LegalCompass AI** is a RAG-based (Retrieval-Augmented Generation) legal assistant designed specifically for Indian Criminal Law. It provides semantic search, case retrieval, and analytics over a massive corpus of Indian legal documents.

It also includes a **Document Summarizer** subsystem that simplifies complex legal jargon into an everyday Class-8 reading level summary.

## Tech Stack & Architecture
- **Backend**: Python, FastAPI (`scripts/api_server.py`)
- **Vector Database**: ChromaDB
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Frontend**: Vanilla HTML, CSS, JavaScript + Chart.js
- **Summarizer**: Groq API (`llama-3.3-70b-versatile`) with a Map-Reduce chunking strategy.

## The Corpus Data (~85,000 embedded chunks)
The system retrieves context from four primary legal datasets:
1. **Bare Acts (2023)**: Official Indian gazettes (BNS, BNSS, BSA).
2. **Case Documents**: Real murder case precedents (IPC 302 / BNS 103).
3. **Crime Statistics**: NCRB district-level crime data.
4. **IL-TUR Benchmark Dataset**: A multi-task legal NLP benchmark dataset containing records for Bail prediction, Court Judgment Prediction, Legal Machine Translation, etc. Exactly 50,000 chunks were sampled from this dataset to maintain performance constraints.

---

## 🚀 Quick Setup Guide

Follow these steps to get LegalCompass AI running on your local machine quickly.

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/piyushpatil1221/LegalCompassAI.git
cd LegalCompassAI

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\Activate.ps1
# Activate it (macOS/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory to enable the summarizer functionality:
```env
GROQ_API_KEY=your_groq_api_key_here
```
*(You can get a free API key at [console.groq.com](https://console.groq.com/keys))*

### 3. Generate the Vector Database
Because the vector database (`chroma_db`) is too large for GitHub, you need to generate it locally.
*Note: This process embeds ~85,000 documents and can take a while on a CPU. It is recommended to run this on a GPU if available.*

```bash
# 1. Chunk the raw datasets
python scripts/chunk_corpus.py

# 2. Embed the chunks into ChromaDB
python scripts/embed_and_index.py
```
This will create a `BNS DATASET/output/chroma_db` folder locally containing the SQLite vectors.

### 4. Run the API Server and Dashboard
Once the database is ready, you can start the FastAPI backend:
```bash
python scripts/api_server.py
```
Open your browser and navigate to:
👉 **http://localhost:8000**

---

## Summarizer Usage

You can also use the summarizer module directly via the CLI:
```bash
python main.py summarize path/to/document.pdf
```
This will parse the legal PDF, run it through the Groq Map-Reduce pipeline, and output a simplified `.docx` or `.pdf` summary next to the source file.
