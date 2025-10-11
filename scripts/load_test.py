# scripts/load_test.py
import asyncio
import aiohttp

async def send_message(session, i):
    payload = {
        "From": f"whatsapp:+1234567{i:04d}",
        "Body": f"Test {i}: When do classes start?",
        "To": "whatsapp:+14155238886"
    }
    async with session.post("https://your-bot.up.railway.app/webhook", data=payload) as r:
        return r.status

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [send_message(session, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        print(f"Success rate: {results.count(200)}/100")

asyncio.run(main())