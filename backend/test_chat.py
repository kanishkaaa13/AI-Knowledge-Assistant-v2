import httpx
import json

async def test_chat():
    try:
        async with httpx.AsyncClient() as client:
            # First, let's try to login to get a token
            login_resp = await client.post(
                'http://127.0.0.1:8000/api/v1/auth/login',
                json={'email': 'kanishkaarde99@gmail.com', 'password': 'test12345'},
                timeout=10.0
            )
            print(f'Login status: {login_resp.status_code}')
            print(f'Login response: {login_resp.text[:200]}')
            
            if login_resp.status_code == 200:
                token = login_resp.json().get('access_token')
                print(f'Token: {token[:20]}...')
                
                # Now try the chat stream endpoint
                chat_resp = await client.post(
                    'http://127.0.0.1:8000/api/v1/assistant/chat/stream',
                    json={'query': 'hello', 'model': 'llama3'},
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=30.0
                )
                print(f'Chat status: {chat_resp.status_code}')
                print(f'Chat response: {chat_resp.text[:500]}')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chat())
