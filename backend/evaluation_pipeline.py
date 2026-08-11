"""
Evaluation Pipeline - Runs test questions through RAG pipeline and logs results.

This script runs a set of test questions through the full RAG pipeline and logs:
- Retrieved chunks (with metadata: document_id, filename, page, score)
- Generated answer
- Whether citations are present in the answer

Output format: JSON report for manual quality assessment.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.assistant_chat import AssistantChatService
from app.services.vector_store import get_vector_store_service


def check_citations_present(answer: str) -> bool:
    """Check if the answer contains source citations.
    
    Citations are expected in format: [Source: filename, Page X, Paragraph Y]
    """
    citation_pattern = r'\[Source:\s*[^,]+,\s*Page\s*\d+'
    return bool(re.search(citation_pattern, answer))


async def run_single_evaluation(
    user: User,
    question: str,
    model: str = "llama3.1",
    top_k: int = 4,
    document_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run a single question through the RAG pipeline and capture results."""
    
    vector_store = get_vector_store_service()
    chat_service = AssistantChatService(vector_store)
    
    result = await chat_service.answer(
        user=user,
        query=question,
        model=model,
        top_k=top_k,
        document_ids=document_ids,
    )
    
    # Extract chunk information
    chunks_info = []
    for chunk in result.get("chunks", []):
        metadata = chunk.get("metadata", {})
        chunks_info.append({
            "document_id": metadata.get("document_id"),
            "filename": metadata.get("filename"),
            "page": metadata.get("page"),
            "chunk_index": metadata.get("chunk_index"),
            "section": metadata.get("section"),
            "content_preview": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
        })
    
    # Check for citations
    has_citations = check_citations_present(result.get("answer", ""))
    
    return {
        "question": question,
        "answer": result.get("answer", ""),
        "context": result.get("context", ""),
        "retrieved_chunks": chunks_info,
        "num_chunks_retrieved": len(chunks_info),
        "has_citations": has_citations,
        "model": model,
        "top_k": top_k,
        "document_ids": document_ids,
    }


async def run_evaluation(
    user_email: str,
    test_questions: list[dict[str, str]],
    model: str = "llama3.1",
    top_k: int = 4,
    output_file: str = "evaluation_results.json",
) -> dict[str, Any]:
    """Run all test questions through the pipeline and generate report."""
    
    # Get user from database
    with next(get_db()) as db:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise ValueError(f"User with email {user_email} not found")
    
    results = []
    timestamp = datetime.now().isoformat()
    
    print(f"Starting evaluation for user: {user_email}")
    print(f"Number of test questions: {len(test_questions)}")
    print(f"Model: {model}, top_k: {top_k}")
    print("-" * 80)
    
    for idx, test_item in enumerate(test_questions, 1):
        question = test_item.get("question")
        expected_answer = test_item.get("expected_answer", "")
        document_ids = test_item.get("document_ids")
        
        print(f"[{idx}/{len(test_questions)}] Processing: {question[:60]}...")
        
        try:
            result = await run_single_evaluation(
                user=user,
                question=question,
                model=model,
                top_k=top_k,
                document_ids=document_ids,
            )
            
            # Add expected answer for comparison
            result["expected_answer"] = expected_answer
            
            results.append(result)
            print(f"  ✓ Retrieved {result['num_chunks_retrieved']} chunks, citations: {result['has_citations']}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "question": question,
                "expected_answer": expected_answer,
                "error": str(e),
                "num_chunks_retrieved": 0,
                "has_citations": False,
            })
    
    # Generate report
    report = {
        "timestamp": timestamp,
        "user_email": user_email,
        "user_id": str(user.id),
        "model": model,
        "top_k": top_k,
        "total_questions": len(test_questions),
        "successful_runs": len([r for r in results if "error" not in r]),
        "failed_runs": len([r for r in results if "error" in r]),
        "results": results,
    }
    
    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("-" * 80)
    print(f"Evaluation complete. Results saved to: {output_file}")
    print(f"Successful: {report['successful_runs']}/{report['total_questions']}")
    print(f"Failed: {report['failed_runs']}/{report['total_questions']}")
    
    return report


# Test questions for relevance threshold evaluation
TEST_QUESTIONS_THRESHOLD = [
    {
        "question": "What is machine learning?",
        "expected_answer": "Machine learning is a subset of artificial intelligence...",
        "document_ids": None,
    },
    {
        "question": "What is agentic AI and how does it differ from traditional AI?",
        "expected_answer": "Agentic AI refers to AI systems that can take autonomous actions...",
        "document_ids": None,
    },
    {
        "question": "What is the capital of Australia?",
        "expected_answer": "Canberra",
        "document_ids": None,
    },
    {
        "question": "What are the steps in risk management?",
        "expected_answer": "Risk management involves identification, assessment, and mitigation...",
        "document_ids": None,
    },
    {
        "question": "What is project management?",
        "expected_answer": "Project management is the practice of planning, executing, and controlling projects...",
        "document_ids": None,
    },
]

# Test questions for boilerplate detection evaluation (with page 16 content)
TEST_QUESTIONS_BOILERPLATE = [
    {
        "question": "What is machine learning?",
        "expected_answer": "Machine learning is a subset of artificial intelligence...",
        "document_ids": None,
    },
    {
        "question": "What are the types of machine learning?",
        "expected_answer": "Types include supervised, unsupervised, and reinforcement learning...",
        "document_ids": None,
    },
    {
        "question": "What is the capital of Australia?",
        "expected_answer": "Canberra",
        "document_ids": None,
    },
]


async def main():
    """Main entry point for evaluation."""
    
    # Configuration - use user with multi-page document for boilerplate testing
    USER_EMAIL = "concurrent2@example.com"  # User with multi-page documents
    MODEL = "llama3.1"
    TOP_K = 4
    OUTPUT_FILE = "evaluation_results_boilerplate.json"
    
    # Test questions for boilerplate detection evaluation
    test_questions = TEST_QUESTIONS_BOILERPLATE
    
    # Run evaluation
    report = await run_evaluation(
        user_email=USER_EMAIL,
        test_questions=test_questions,
        model=MODEL,
        top_k=TOP_K,
        output_file=OUTPUT_FILE,
    )
    
    # Print summary
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total questions: {report['total_questions']}")
    print(f"Successful runs: {report['successful_runs']}")
    print(f"Failed runs: {report['failed_runs']}")
    
    # Citation statistics
    successful_results = [r for r in report['results'] if "error" not in r]
    if successful_results:
        with_citations = len([r for r in successful_results if r['has_citations']])
        print(f"Answers with citations: {with_citations}/{len(successful_results)}")
        
        avg_chunks = sum(r['num_chunks_retrieved'] for r in successful_results) / len(successful_results)
        print(f"Average chunks retrieved: {avg_chunks:.1f}")


if __name__ == "__main__":
    asyncio.run(main())
