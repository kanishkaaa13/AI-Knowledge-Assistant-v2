"""
Show the specific diff for rag_pipeline.py fallback removal
"""

print("Diff for rag_pipeline.py fallback removal:")
print("=" * 80)
print()

print("BEFORE (lines 233-236):")
print("-" * 40)
print("        # Fallback to single page using extracted text if parsing returns empty list")
print("        if not pages:")
print("            from app.services.document_parser import ParsedDocumentPage")
print("            pages = [ParsedDocumentPage(page_number=1, text=document.extracted_text or \"\")]")
print()

print("AFTER (lines 233-238):")
print("-" * 40)
print("        # If parsing returns empty list, fail with clear error")
print("        if not pages:")
print("            raise HTTPException(")
print("                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,")
print("                detail=\"Document parsing returned no pages. The file may be corrupted or in an unsupported format.\"")
print("            )")
print()

print("=" * 80)
print("SUMMARY:")
print("  - Removed: Silent fallback to synthetic single-page document")
print("  - Added: HTTPException with 422 status and clear error message")
print("  - Behavior: Decryption/parsing failures now surface as errors instead of")
print("              being silently degraded to single-page mode")
print("=" * 80)
