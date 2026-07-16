import unittest
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.okf_record import OKFRecord
from app.models.user import User

class TestOKFEndpoints(unittest.TestCase):
    def setUp(self):
        # Create mock user
        self.mock_user = User(
            id=uuid.uuid4(),
            name="Test User",
            email="testuser@example.com",
            hashed_password="fakehashedpassword"
        )
        
        # Mock database session
        self.mock_db = MagicMock()
        
        # Override FastAPI dependencies for testing
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: self.mock_db
        
        self.client = TestClient(app)

    def tearDown(self):
        # Clear dependency overrides
        app.dependency_overrides.clear()

    def test_list_okf_records_success(self):
        # Setup mock OKF record
        mock_record_1 = OKFRecord(
            id=uuid.uuid4(),
            source_document_id=uuid.uuid4(),
            file_path="okf_bundles/doc1/concept1.md",
            type="concept",
            title="Concept 1",
            tags=["tag1", "tag2"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock SQLAlchemy execution return values
        self.mock_db.scalar.return_value = 1
        
        mock_scalars_all = MagicMock()
        mock_scalars_all.all.return_value = [mock_record_1]
        self.mock_db.scalars.return_value = mock_scalars_all
        
        response = self.client.get("/api/v1/okf?page=1&page_size=10")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["title"], "Concept 1")
        self.assertEqual(data["items"][0]["type"], "concept")

    @patch("app.api.okf.parse_okf")
    @patch("app.api.okf.Path.exists")
    @patch("app.api.okf.Path.read_text")
    def test_get_okf_document_success(self, mock_read_text, mock_exists, mock_parse_okf):
        record_id = uuid.uuid4()
        source_doc_id = uuid.uuid4()
        
        mock_record = OKFRecord(
            id=record_id,
            source_document_id=source_doc_id,
            file_path="okf_bundles/doc1/concept1.md",
            type="concept",
            title="Concept 1",
            tags=["tag1"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # db.scalar(stmt) for record query
        self.mock_db.scalar.return_value = mock_record
        
        # Mock file system checks
        mock_exists.return_value = True
        mock_read_text.return_value = "---\ntype: concept\ntitle: Concept 1\n---"
        
        # Mock parser return value
        from app.okf.schema import OKFDocument
        mock_okf_doc = OKFDocument(
            type="concept",
            title="Concept 1",
            tags=["tag1"],
            related=[],
            source_document_id=str(source_doc_id),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            body="This is the parsed concept body"
        )
        mock_parse_okf.return_value = mock_okf_doc
        
        response = self.client.get(f"/api/v1/okf/{record_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Concept 1")
        self.assertEqual(data["body"], "This is the parsed concept body")
        self.assertEqual(data["source_document_id"], str(source_doc_id))

    def test_get_okf_document_not_found(self):
        # db.scalar(stmt) returns None
        self.mock_db.scalar.return_value = None
        
        response = self.client.get(f"/api/v1/okf/{uuid.uuid4()}")
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("OKF Record not found", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
