"""Unified launcher for the LegalCompassAI + Summarizer project."""

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LEGAL_REQUIRED = [
    "fastapi",
    "uvicorn",
    "sentence_transformers",
    "chromadb",
    "pydantic",
    "numpy",
    "scikit_learn",
    "torch",
]


def _missing_requirements(packages):
    missing = []
    for pkg in packages:
        module_name = pkg.replace("-", "_")
        if importlib.util.find_spec(module_name) is None:
            missing.append(pkg)
    return missing


def ensure_legal_dependencies():
    missing = _missing_requirements(LEGAL_REQUIRED)
    if not missing:
        return

    print(f"Missing required legal app dependencies: {', '.join(missing)}")
    print("Installing from project requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])


def run_summarizer(input_path: str):
    from extract_text import extract_text
    from LegalCompassAI.summarize import summarize_text
    from LegalCompassAI.save_output import save_summary_docx

    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)

    print(f"Extracting text from {input_path}...")
    text = extract_text(input_path)
    print(f"Extracted {len(text)} characters.")

    print("Summarizing and simplifying...")
    summary = summarize_text(text)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(os.path.dirname(input_path) or ".", f"{base_name}_summary.docx")

    save_summary_docx(summary, output_path, source_filename=os.path.basename(input_path))
    print(f"\nDone. Wrote {output_path}")
    return output_path


def run_legal_app(host: str = "0.0.0.0", port: int = 8000):
    ensure_legal_dependencies()
    import uvicorn

    os.chdir(ROOT)
    uvicorn.run("LegalCompassAI.scripts.api_server:app", host=host, port=port, reload=False)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run either the legal research app or the document summarizer from one project root."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Turn a PDF or DOCX into a simplified, formatted .docx summary.",
    )
    summarize_parser.add_argument("input_path", help="Path to the input PDF or DOCX file")

    legal_parser = subparsers.add_parser(
        "legal",
        help="Start the LegalCompassAI API and web interface on localhost:8000.",
    )
    legal_parser.add_argument("--host", default="0.0.0.0")
    legal_parser.add_argument("--port", type=int, default=8000)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "summarize":
        run_summarizer(args.input_path)
        return 0

    if args.command == "legal":
        run_legal_app(host=args.host, port=args.port)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
