import unittest
from datetime import datetime
from pydantic import ValidationError
from app.okf.schema import OKFDocument
from app.okf.parser import parse_okf, serialize_okf

class TestOKFParser(unittest.TestCase):
    def test_valid_parse(self):
        raw_text = """---
type: concept
title: Introduction to OKF
tags:
  - okf
  - schema
related:
  - other_doc
source_document_id: doc-123
created_at: 2026-07-03T03:02:14
updated_at: 2026-07-03T03:02:14
---
# OKF Guide
This is the body of the OKF document.
It has multiple lines.
"""
        doc = parse_okf(raw_text)
        self.assertEqual(doc.type, "concept")
        self.assertEqual(doc.title, "Introduction to OKF")
        self.assertEqual(doc.tags, ["okf", "schema"])
        self.assertEqual(doc.related, ["other_doc"])
        self.assertEqual(doc.source_document_id, "doc-123")
        # pyyaml parses ISO timestamps to python datetime
        self.assertEqual(doc.created_at.replace(tzinfo=None), datetime(2026, 7, 3, 3, 2, 14))
        self.assertEqual(doc.updated_at.replace(tzinfo=None), datetime(2026, 7, 3, 3, 2, 14))
        self.assertEqual(doc.body, "# OKF Guide\nThis is the body of the OKF document.\nIt has multiple lines.\n")

    def test_missing_type_raises_validation_error(self):
        raw_text_missing_type = """---
title: Introduction to OKF
tags:
  - okf
related: []
source_document_id: null
created_at: 2026-07-03T03:02:14
updated_at: 2026-07-03T03:02:14
---
This has no type.
"""
        with self.assertRaises(ValidationError):
            parse_okf(raw_text_missing_type)

    def test_round_trip(self):
        original_doc = OKFDocument(
            type="policy",
            title="Data Privacy Policy",
            tags=["privacy", "compliance"],
            related=["terms_of_service"],
            source_document_id="doc-999",
            created_at=datetime(2026, 7, 3, 3, 0, 0),
            updated_at=datetime(2026, 7, 3, 3, 30, 0),
            body="# Data Privacy\nDetailed policy guidelines here.\n"
        )
        
        # Serialize to string
        serialized_str = serialize_okf(original_doc)
        
        # Parse back to OKFDocument
        parsed_doc = parse_okf(serialized_str)
        
        # Check equality of all fields
        self.assertEqual(original_doc.type, parsed_doc.type)
        self.assertEqual(original_doc.title, parsed_doc.title)
        self.assertEqual(original_doc.tags, parsed_doc.tags)
        self.assertEqual(original_doc.related, parsed_doc.related)
        self.assertEqual(original_doc.source_document_id, parsed_doc.source_document_id)
        self.assertEqual(original_doc.created_at.replace(tzinfo=None), parsed_doc.created_at.replace(tzinfo=None))
        self.assertEqual(original_doc.updated_at.replace(tzinfo=None), parsed_doc.updated_at.replace(tzinfo=None))
        self.assertEqual(original_doc.body, parsed_doc.body)

if __name__ == "__main__":
    unittest.main()
