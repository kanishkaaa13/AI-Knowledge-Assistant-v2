import os
import sys
import asyncio
from pathlib import Path

# Add backend directory to Python path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

# Force load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=backend_dir / ".env")

from app.services.okf_retriever import OKFRetrieverService


async def test_retrieve(bundle_path_str: str, query: str):
    bundle_path = Path(bundle_path_str)
    if not bundle_path.exists() or not bundle_path.is_dir():
        print(f"Error: OKF bundle directory '{bundle_path_str}' does not exist or is not a directory.")
        sys.exit(1)
        
    print(f"Querying bundle: {bundle_path.name}")
    print(f"User Query: \"{query}\"\n")
    
    retriever = OKFRetrieverService()
    try:
        results = await retriever.retrieve_concepts(bundle_path_str, query)
        
        if not results:
            print("No matching concept files retrieved.")
            return
            
        print("="*80)
        print(f" RETRIEVED CONCEPTS ({len(results)} found)")
        print("="*80)
        
        for idx, item in enumerate(results, start=1):
            print(f"\n[{idx}] File: {item['filename']} (Retrieved via: {item['retrieved_via']})")
            print(f"    Title:       {item['title']}")
            print(f"    Description: {item['description']}")
            print(f"    Tags:        {', '.join([f'#{t}' for t in item['tags']])}")
            print(f"    Filepath:    {item['filepath']}")
            print("    " + "-"*40)
            
            # Print body excerpt (first 5 lines or 300 chars)
            body_lines = item['body'].splitlines()
            excerpt = "\n".join([f"      {line}" for line in body_lines[:6]])
            print(excerpt)
            if len(body_lines) > 6:
                print("      ...")
            print("    " + "-"*40)
            
        print("\n" + "="*80)
        
    except Exception as exc:
        import traceback
        print(f"Error during OKF retrieval: {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_okf_retrieve.py <path_to_okf_bundle> <query_string>")
        sys.exit(1)
        
    target_bundle = sys.argv[1]
    query_str = sys.argv[2]
    asyncio.run(test_retrieve(target_bundle, query_str))
