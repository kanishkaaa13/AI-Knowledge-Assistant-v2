"""
Migration script to re-encrypt existing unencrypted files

This script:
1. Scans all uploaded documents
2. Detects which files are unencrypted (valid PDF/docx/txt/md headers)
3. Re-encrypts them using the encryption service
4. Writes them back to disk

SAFETY: Run with --dry-run first to see what would be changed
"""

import sys
import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.core.crypto import encryption_service


def is_pdf_valid(file_bytes: bytes) -> bool:
    """Check if bytes are a valid PDF."""
    try:
        reader = PdfReader(BytesIO(file_bytes))
        return len(reader.pages) > 0
    except Exception:
        return False


def is_docx_valid(file_bytes: bytes) -> bool:
    """Check if bytes are a valid DOCX."""
    # DOCX files are ZIP archives with specific structure
    try:
        from zipfile import ZipFile
        from io import BytesIO
        with ZipFile(BytesIO(file_bytes)) as zf:
            # Check for required DOCX files
            return '[Content_Types].xml' in zf.namelist()
    except Exception:
        return False


def is_text_valid(file_bytes: bytes) -> bool:
    """Check if bytes are valid text (txt/md)."""
    try:
        text = file_bytes.decode('utf-8')
        return len(text) > 0
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode('latin-1')
            return len(text) > 0
        except Exception:
            return False


def is_unencrypted(file_bytes: bytes, file_extension: str) -> bool:
    """Check if file bytes are unencrypted (valid file format)."""
    if file_extension == '.pdf':
        return is_pdf_valid(file_bytes)
    elif file_extension == '.docx':
        return is_docx_valid(file_bytes)
    elif file_extension in {'.txt', '.md'}:
        return is_text_valid(file_bytes)
    return False


def migrate_document(doc: UploadedDocument, dry_run: bool = True) -> dict:
    """Migrate a single document to encrypted storage."""
    result = {
        'document_id': str(doc.id),
        'filename': doc.file_name,
        'action': 'skip',
        'reason': '',
        'error': None
    }
    
    file_path = Path(doc.file_path)
    if not file_path.exists():
        result['action'] = 'error'
        result['reason'] = 'File not found on disk'
        return result
    
    # Read current bytes
    raw_bytes = file_path.read_bytes()
    
    # Check if already encrypted
    if not is_unencrypted(raw_bytes, doc.file_extension):
        result['action'] = 'skip'
        result['reason'] = 'Already encrypted'
        return result
    
    result['action'] = 'encrypt'
    
    if dry_run:
        result['reason'] = 'Would encrypt (dry-run)'
        return result
    
    try:
        # Encrypt the bytes
        encrypted_bytes = encryption_service.encrypt_bytes(raw_bytes)
        
        # Write back to disk
        file_path.write_bytes(encrypted_bytes)
        
        # Verify decryption works
        decrypted = encryption_service.decrypt_bytes(encrypted_bytes)
        if decrypted != raw_bytes:
            result['action'] = 'error'
            result['reason'] = 'Decryption verification failed'
            return result
        
        result['reason'] = 'Successfully encrypted'
        return result
        
    except Exception as e:
        result['action'] = 'error'
        result['reason'] = f'Encryption failed: {e}'
        result['error'] = str(e)
        return result


def main():
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 80)
        print()
    else:
        print("=" * 80)
        print("WARNING: This will RE-ENCRYPT all unencrypted files")
        print("Run with --dry-run first to see what will be changed")
        print()
        response = input("Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
        print()
    
    with next(get_db()) as db:
        documents = db.query(UploadedDocument).all()
        
        print(f"Scanning {len(documents)} documents...")
        print()
        
        results = {
            'total': len(documents),
            'unencrypted': 0,
            'already_encrypted': 0,
            'errors': 0,
            'details': []
        }
        
        for doc in documents:
            result = migrate_document(doc, dry_run=dry_run)
            results['details'].append(result)
            
            if result['action'] == 'encrypt':
                results['unencrypted'] += 1
                print(f"  [ENCRYPT] {doc.file_name} ({result['reason']})")
            elif result['action'] == 'skip':
                if 'Already encrypted' in result['reason']:
                    results['already_encrypted'] += 1
                else:
                    print(f"  [SKIP] {doc.file_name} ({result['reason']})")
            elif result['action'] == 'error':
                results['errors'] += 1
                print(f"  [ERROR] {doc.file_name}: {result['reason']}")
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total documents: {results['total']}")
        print(f"Unencrypted (would encrypt): {results['unencrypted']}")
        print(f"Already encrypted: {results['already_encrypted']}")
        print(f"Errors: {results['errors']}")
        print()
        
        if results['unencrypted'] > 0 and not dry_run:
            print(f"Successfully re-encrypted {results['unencrypted']} files")
        elif results['unencrypted'] > 0 and dry_run:
            print(f"Would re-encrypt {results['unencrypted']} files")
            print("Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()
