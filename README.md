# LegalCompassAI + Document Summarizer

This project now combines the legal research application and the document summarizer into one project root.

## What is included
- LegalCompassAI legal RAG app and web UI under `LegalCompassAI/`
- Document summarizer pipeline using Groq + PDF/DOCX extraction under the root project
- One launcher at `main.py` to run both parts from the same environment

## Setup
```bash
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows PowerShell:
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

For the summarizer, set a Groq API key:
```bash
export GROQ_API_KEY=gsk_...
# Windows PowerShell:
# $env:GROQ_API_KEY = "gsk_..."
```

You can also create a `.env` file in the project root with:
```env
GROQ_API_KEY=gsk_...
```

## Run the combined project

### 1) Summarize a legal document
```bash
python main.py summarize path/to/document.pdf
python main.py summarize path/to/document.docx
```
This writes a file next to the source, such as `document_summary.docx`.

### 2) Start the LegalCompassAI app
```bash
python main.py legal
```
Open:
```text
http://localhost:8000
```

## Project layout
- `main.py` — unified launcher for both workflows
- `extract_text.py` — PDF/DOCX text extraction
- `summarize.py` — Groq-based simplification and chunk merging
- `save_output.py` — writes the summary as a `.docx` file
- `LegalCompassAI/` — legal corpus, retriever, API, and webapp

## How the summarizer works
1. `extract_text.py` reads raw text from a PDF or DOCX
2. `summarize.py` chunks long content and simplifies it with Groq
3. `save_output.py` writes the final rewritten summary to a Word document
4. `main.py` connects the pieces together and exposes the legal app entry point

## Notes
- The original summarizer flow remains compatible with its previous CLI usage.
- The LegalCompassAI web app remains available from the same workspace and can be started via the root launcher.
