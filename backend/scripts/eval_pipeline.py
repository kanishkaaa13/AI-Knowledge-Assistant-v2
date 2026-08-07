#!/usr/bin/env python3
"""
Evaluation Pipeline - Read-only eval logger for RAG pipeline quality assessment.

This script runs test questions through the existing RAG pipeline and logs raw results
for manual quality assessment. It does NOT modify any production pipeline logic.

Usage:
    python scripts/eval_pipeline.py

Requirements:
    - backend/scripts/test_questions.json must exist with test questions
    - Database must be accessible
    - Ollama service must be running for the specified model
"""

import asyncio
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.assistant_chat import AssistantChatService
from app.services.vector_store import get_vector_store_service


# Configuration
SCRIPT_DIR = Path(__file__).parent
TEST_QUESTIONS_FILE = SCRIPT_DIR / "test_questions.json"
RESULTS_JSON_FILE = SCRIPT_DIR / "eval_results.json"
RESULTS_CSV_FILE = SCRIPT_DIR / "eval_results.csv"
USER_EMAIL = "kanishkaarde90@gmail.com"  # Target user with indexed documents
MODEL = "llama3:latest"
TOP_K = 4


def check_citations_present(answer: str) -> bool:
    """
    Check if the answer contains source citations.
    
    PROVISIONAL citation detection - checks for bracketed "Source:" or "Page" patterns.
    User will confirm exact format after seeing real outputs.
    
    Expected format based on code inspection: [Source: filename, Page X, Paragraph Y]
    """
    # Check for bracketed citation patterns
    citation_patterns = [
        r'\[Source:\s*[^,]+,\s*Page\s*\d+',  # [Source: filename, Page X]
        r'\[Source:',  # Any bracketed Source reference
        r'\[Page\s*\d+',  # Any bracketed Page reference
    ]
    
    for pattern in citation_patterns:
        if re.search(pattern, answer):
            return True
    return False


def extract_chunk_info(chunk: dict[str, Any]) -> dict[str, Any]:
    """
    Extract relevant information from a chunk for evaluation logging.
    
    Args:
        chunk: Chunk dict with 'content' and 'metadata' keys
        
    Returns:
        Dict with chunk_text, source_document, page_number, similarity_score_unavailable
    """
    metadata = chunk.get("metadata", {})
    
    return {
        "chunk_text": chunk.get("content", ""),
        "source_document": metadata.get("filename", "Unknown"),
        "page_number": metadata.get("page"),
        "similarity_score_unavailable": "not_exposed_by_pipeline",
    }


async def run_single_question(
    user: User,
    question_data: dict[str, str],
    chat_service: AssistantChatService,
) -> dict[str, Any]:
    """
    Run a single question through the RAG pipeline and capture results.
    
    Args:
        user: User object for the test user
        question_data: Dict with id, question, expected_answer, source_document
        chat_service: AssistantChatService instance
        
    Returns:
        Dict with evaluation results for this question
    """
    question_id = question_data.get("id", "unknown")
    question = question_data.get("question", "")
    expected_answer = question_data.get("expected_answer", "")
    source_document = question_data.get("source_document", "")
    
    start_time = time.time()
    
    try:
        # Call the existing pipeline function
        result = await chat_service.answer(
            user=user,
            query=question,
            model=MODEL,
            top_k=TOP_K,
            document_ids=None,  # Search all documents
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract chunk information
        retrieved_chunks = []
        for chunk in result.get("chunks", []):
            retrieved_chunks.append(extract_chunk_info(chunk))
        
        # Check for citations
        generated_answer = result.get("answer", "")
        citations_present = check_citations_present(generated_answer)
        
        return {
            "question_id": question_id,
            "question": question,
            "expected_answer": expected_answer,
            "source_document": source_document,
            "retrieved_chunks": retrieved_chunks,
            "generated_answer": generated_answer,
            "citations_present": citations_present,
            "latency_ms": round(latency_ms, 2),
            "error": None,
        }
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "question_id": question_id,
            "question": question,
            "expected_answer": expected_answer,
            "source_document": source_document,
            "retrieved_chunks": [],
            "generated_answer": "",
            "citations_present": False,
            "latency_ms": round(latency_ms, 2),
            "error": str(e),
        }


def write_json_results(results: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    """Write full detailed results to JSON file."""
    output = {
        "metadata": metadata,
        "results": results,
    }
    
    with open(RESULTS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"JSON results written to: {RESULTS_JSON_FILE}")


def write_csv_results(results: list[dict[str, Any]]) -> None:
    """Write flattened results to CSV file (one row per question)."""
    fieldnames = [
        "question_id",
        "question",
        "expected_answer",
        "source_document",
        "retrieved_chunks_summary",
        "num_chunks_retrieved",
        "generated_answer",
        "citations_present",
        "latency_ms",
        "error",
    ]
    
    with open(RESULTS_CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            # Flatten chunks to a summary string
            chunks_summary = "; ".join([
                f"{c['source_document']}:page{c['page_number']}" 
                for c in result.get("retrieved_chunks", [])
            ])
            
            writer.writerow({
                "question_id": result.get("question_id"),
                "question": result.get("question"),
                "expected_answer": result.get("expected_answer"),
                "source_document": result.get("source_document"),
                "retrieved_chunks_summary": chunks_summary,
                "num_chunks_retrieved": len(result.get("retrieved_chunks", [])),
                "generated_answer": result.get("generated_answer"),
                "citations_present": result.get("citations_present"),
                "latency_ms": result.get("latency_ms"),
                "error": result.get("error"),
            })
    
    print(f"CSV results written to: {RESULTS_CSV_FILE}")


async def main() -> None:
    """Main evaluation pipeline execution."""
    
    # Load test questions
    if not TEST_QUESTIONS_FILE.exists():
        print(f"Error: Test questions file not found: {TEST_QUESTIONS_FILE}")
        print("Please create backend/scripts/test_questions.json with your test questions.")
        return
    
    with open(TEST_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        test_questions = json.load(f)
    
    print(f"Loaded {len(test_questions)} test questions from {TEST_QUESTIONS_FILE}")
    
    # Get user from database
    with next(get_db()) as db:
        user = db.query(User).filter(User.email == USER_EMAIL).first()
        if not user:
            print(f"Error: User with email {USER_EMAIL} not found in database")
            return
    
    print(f"Running evaluation for user: {USER_EMAIL} (ID: {user.id})")
    print(f"Model: {MODEL}, top_k: {TOP_K}")
    print("-" * 80)
    
    # Initialize chat service
    vector_store = get_vector_store_service()
    chat_service = AssistantChatService(vector_store)
    
    # Run evaluation for each question
    results = []
    for idx, question_data in enumerate(test_questions, 1):
        question = question_data.get("question", "")
        print(f"[{idx}/{len(test_questions)}] Processing: {question[:60]}...")
        
        result = await run_single_question(user, question_data, chat_service)
        results.append(result)
        
        if result.get("error"):
            print(f"  ✗ Error: {result['error']}")
        else:
            print(f"  ✓ Retrieved {len(result['retrieved_chunks'])} chunks, "
                  f"citations: {result['citations_present']}, "
                  f"latency: {result['latency_ms']:.0f}ms")
    
    # Write results
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "user_email": USER_EMAIL,
        "user_id": str(user.id),
        "model": MODEL,
        "top_k": TOP_K,
        "total_questions": len(test_questions),
    }
    
    write_json_results(results, metadata)
    write_csv_results(results)
    
    # Print summary
    successful = len([r for r in results if not r.get("error")])
    failed = len([r for r in results if r.get("error")])
    with_citations = len([r for r in results if r.get("citations_present")])
    
    print("-" * 80)
    print("EVALUATION COMPLETE")
    print(f"Total questions: {len(test_questions)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"With citations: {with_citations}")


if __name__ == "__main__":
    asyncio.run(main())
