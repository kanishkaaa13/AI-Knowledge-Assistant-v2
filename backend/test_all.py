import httpx
import json
import asyncio

BASE = "http://127.0.0.1:8001"

async def test_all():
    print("Testing All Features...")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Login
            login_resp = await client.post(
                f'{BASE}/api/v1/auth/login',
                json={'email': 'kanishkaarde99@gmail.com', 'password': 'test12345'}
            )
            if login_resp.status_code != 200:
                print(f"Login failed: {login_resp.text}")
                return
            
            token = login_resp.json().get('access_token')
            headers = {'Authorization': f'Bearer {token}'}

            # Get Documents to find Unit 3
            docs_resp = await client.get(f'{BASE}/api/v1/documents', headers=headers)
            docs = docs_resp.json().get('items', [])
            unit3_doc = next((d for d in docs if 'Unit 3' in d.get('title', '') or 'Unit 3' in d.get('filename', '')), None)
            doc_ids = [unit3_doc['id']] if unit3_doc else []
            print(f"Using Unit 3 Doc ID: {doc_ids}")

            # 1. Chat Feature
            print("\n--- 1. Chat Feature ---")
            chat_resp = await client.post(
                f'{BASE}/api/v1/assistant/query',
                json={'query': 'Hello! How are you?', 'model': 'llama3'},
                headers=headers
            )
            print(f"Status: {chat_resp.status_code}")
            if chat_resp.status_code == 200:
                print(f"AI Response: {chat_resp.json().get('answer')}")
            else:
                print(chat_resp.text)

            # 2. Summarize Feature
            print("\n--- 2. Summarize Feature ---")
            sum_resp = await client.post(
                f'{BASE}/api/v1/assistant/summaries',
                json={'query': 'Summarize Unit 3', 'model': 'llama3', 'document_ids': doc_ids},
                headers=headers
            )
            print(f"Status: {sum_resp.status_code}")
            if sum_resp.status_code == 200:
                print(f"Summary: {sum_resp.json().get('summary')[:500]}...")
            else:
                print(sum_resp.text)

            # 3. Quiz Feature
            print("\n--- 3. Quiz Feature ---")
            quiz_resp = await client.post(
                f'{BASE}/api/v1/assistant/quiz',
                json={'query': 'Generate a quiz for Unit 3', 'model': 'llama3', 'document_ids': doc_ids},
                headers=headers
            )
            print(f"Status: {quiz_resp.status_code}")
            if quiz_resp.status_code == 200:
                questions = quiz_resp.json().get('questions', [])
                print(f"Found {len(questions)} questions.")
                for q in questions:
                    print(f"Q: {q.get('question')}")
            else:
                print(quiz_resp.text)

            # 4. Search Feature
            print("\n--- 4. Search Feature ---")
            search_resp = await client.post(
                f'{BASE}/api/v1/assistant/document-search',
                json={'query': 'machine learning', 'model': 'llama3'},
                headers=headers
            )
            print(f"Status: {search_resp.status_code}")
            if search_resp.status_code == 200:
                results = search_resp.json().get('results', [])
                print(f"Found {len(results)} search results.")
                for r in results:
                    print(f" - {r.get('title')} (score: {r.get('score')})")
            else:
                print(search_resp.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_all())
