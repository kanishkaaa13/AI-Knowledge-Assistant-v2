import httpx
import asyncio

async def check_ollama():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get('http://localhost:11434', timeout=2.0)
            print(f'Ollama status: {resp.status_code}')
            print(f'Ollama response: {resp.text}')
    except Exception as e:
        print(f'Ollama connection failed: {e}')

if __name__ == "__main__":
    asyncio.run(check_ollama())
