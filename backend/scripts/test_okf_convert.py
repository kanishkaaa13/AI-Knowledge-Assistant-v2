import os
import sys
import uuid
import asyncio
from pathlib import Path

# Add backend directory to Python path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

# Force load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=backend_dir / ".env")

from app.services.document_processor import DocumentProcessor
from app.services.okf_converter import OKFConverterService


async def test_convert(file_path_str: str):
    file_path = Path(file_path_str)
    if not file_path.exists():
        print(f"Error: File '{file_path_str}' does not exist.")
        sys.exit(1)
        
    print(f"Reading file: {file_path.name}")
    file_bytes = file_path.read_bytes()
    file_extension = file_path.suffix.lower()
    
    print("Extracting text using existing DocumentProcessor...")
    try:
        processor = DocumentProcessor()
        text, page_count = processor.extract_text(file_bytes, file_extension)
        print(f"Extraction successful! Extracted {len(text)} characters (pages/sections count: {page_count or 'N/A'})")
    except Exception as exc:
        print(f"Error extracting text: {exc}")
        sys.exit(1)
        
    if not text.strip():
        print("Error: Extracted text is empty. Cannot convert.")
        sys.exit(1)
        
    mock_document_id = str(uuid.uuid4())
    document_title = file_path.stem.replace("-", " ").replace("_", " ").title()
    
    print("\nStarting OKF conversion pipeline...")
    print("Generating YAML metadata and markdown sections (calling LLM)...")
    
    converter = OKFConverterService()
    try:
        bundle_path = await converter.convert_to_okf_bundle(
            document_id=mock_document_id,
            document_title=document_title,
            text=text
        )
        print("\n" + "="*80)
        print(" OKF CONVERSION SUCCESSFUL!")
        print(f" Bundle Path: {bundle_path.resolve()}")
        print("-"*80)
        print(" Generated Files:")
        for f in sorted(bundle_path.glob("*")):
            print(f"   - {f.name} ({f.stat().st_size} bytes)")
        print("="*80 + "\n")
    except Exception as exc:
        import traceback
        print(f"Error during OKF bundle conversion: {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_okf_convert.py <path_to_document>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    asyncio.run(test_convert(target_file))
