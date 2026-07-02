import unittest
import uuid
from unittest.mock import MagicMock
from app.services.vector_store import VectorStoreService, VectorSearchResult, get_vector_store_service

class TestOKFFiltering(unittest.IsolatedAsyncioTestCase):
    async def test_filtering_logic_in_similarity_search(self):
        service = get_vector_store_service()
        
        # Mock the Chroma collection
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10
        mock_collection.query.return_value = {
            "ids": [["id1", "id2", "id3"]],
            "documents": [["Doc 1", "Doc 2", "Doc 3"]],
            "metadatas": [[
                {"document_id": "doc1", "okf_type": "concept", "okf_tags": "tag1,tag2"},
                {"document_id": "doc2", "okf_type": "api", "okf_tags": "tag3"},
                {"document_id": "doc3", "okf_type": "concept", "okf_tags": "tag1"}
            ]],
            "distances": [[0.1, 0.2, 0.3]]
        }
        
        # Inject the mock collection getter
        service._get_or_create_collection = MagicMock(return_value=mock_collection)
        
        # 1. Search with filter type='concept'
        res = await service.similarity_search(
            user_id=uuid.uuid4(),
            query="test",
            top_k=4,
            filters={"type": "concept"}
        )
        # Should filter and return doc1 and doc3
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].id, "id1")
        self.assertEqual(res[1].id, "id3")
        
        # 2. Search with tags='tag1'
        res2 = await service.similarity_search(
            user_id=uuid.uuid4(),
            query="test",
            top_k=4,
            filters={"tags": "tag1"}
        )
        # Should return doc1 and doc3
        self.assertEqual(len(res2), 2)
        self.assertEqual(res2[0].id, "id1")
        self.assertEqual(res2[1].id, "id3")

        # 3. Search with tags='tag2'
        res3 = await service.similarity_search(
            user_id=uuid.uuid4(),
            query="test",
            top_k=4,
            filters={"tags": "tag2"}
        )
        # Should return only doc1
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0].id, "id1")

if __name__ == "__main__":
    unittest.main()
