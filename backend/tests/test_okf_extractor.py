import unittest
from unittest.mock import patch, AsyncMock
from app.services.okf_extractor import extract_okf_concepts
from app.okf.schema import OKFDocument

class TestOKFExtractor(unittest.IsolatedAsyncioTestCase):
    @patch("app.services.okf_extractor.OllamaLLMService")
    async def test_extract_okf_concepts_success(self, mock_ollama_class):
        # Setup mock LLM response
        mock_ollama_instance = mock_ollama_class.return_value
        mock_ollama_instance.generate = AsyncMock(return_value="""```json
[
  {
    "type": "concept",
    "title": "Machine Learning",
    "tags": ["ml", "ai"],
    "related": ["Deep Learning"],
    "body": "Machine learning is a subset of artificial intelligence."
  },
  {
    "type": "api",
    "title": "Predict API",
    "tags": ["endpoint", "prediction"],
    "related": ["Machine Learning"],
    "body": "POST /predict to run predictions."
  }
]
```""")

        docs = await extract_okf_concepts(
            document_text="This is text containing Machine Learning and Predict API.",
            source_document_id="doc-111"
        )
        
        self.assertEqual(len(docs), 2)
        
        # Verify first document
        self.assertEqual(docs[0].type, "concept")
        self.assertEqual(docs[0].title, "Machine Learning")
        self.assertEqual(docs[0].tags, ["ml", "ai"])
        self.assertEqual(docs[0].related, ["Deep Learning"])
        self.assertEqual(docs[0].source_document_id, "doc-111")
        self.assertEqual(docs[0].body, "Machine learning is a subset of artificial intelligence.")
        self.assertTrue(isinstance(docs[0], OKFDocument))
        
        # Verify second document
        self.assertEqual(docs[1].type, "api")
        self.assertEqual(docs[1].title, "Predict API")
        self.assertEqual(docs[1].tags, ["endpoint", "prediction"])
        self.assertEqual(docs[1].related, ["Machine Learning"])
        self.assertEqual(docs[1].source_document_id, "doc-111")
        self.assertEqual(docs[1].body, "POST /predict to run predictions.")
        self.assertTrue(isinstance(docs[1], OKFDocument))

    @patch("app.services.okf_extractor.OllamaLLMService")
    async def test_extract_okf_concepts_graceful_handling_malformed(self, mock_ollama_class):
        # Setup mock LLM response where one concept is malformed (missing required body/title etc.)
        mock_ollama_instance = mock_ollama_class.return_value
        mock_ollama_instance.generate = AsyncMock(return_value="""[
  {
    "type": "concept",
    "title": "Valid Concept",
    "tags": ["tag1"],
    "related": [],
    "body": "This is valid."
  },
  {
    "type": "concept",
    "tags": ["malformed"]
  }
]""")

        docs = await extract_okf_concepts(
            document_text="Some text",
            source_document_id="doc-111"
        )
        
        # Should successfully skip the malformed concept and return only the valid one
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "Valid Concept")
        self.assertEqual(docs[0].body, "This is valid.")
        self.assertTrue(isinstance(docs[0], OKFDocument))

if __name__ == "__main__":
    unittest.main()
