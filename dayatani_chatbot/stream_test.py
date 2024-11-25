import asyncio
import aiohttp
import json

async def fetch_events():
    url = "http://127.0.0.1:8000/api/v1/chat/"
    payload = json.dumps({
        "conversations": "how to grow rince show in steps"
    })

    headers = {
        'Authorization': 'Bearer U2FsdGVkX18/wFLF+aZgja9mC5RxQIe8hJRpSArMGwTVZXQ6cUCmEK5EJaQpJ1hws5TOQFAGnMTYqrcZQe1O47RzO5ioxd+iHD4N99wWEg3aDZkJsWJ+Rdv6QDfPgAYo7o1JgknUZ/WljZ1Qk58r+aGfd9mW2nxYR7Yd2ENfIWquVTGDgVK3FnGsHw32tKb8NiM/+R+n/XTKWEI2+wBwJniRKoEiq38Jw9fNennIo8eKStT+Jz8mgaBQCBccM0o9OFtXv+57FyWgCMLk5/GD5Ot7DUNRJIP0ywOw9AqQugxFFuux2Vqy6/NmUqgWo+tyHv0JdhVEtCBodvPCVAEVfXgh1Jf6gNpcEV33naDHJ+9rInFY4cRxIj1fSQt/avB6',
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            async for segment in response.content.iter_any():
                yield segment

async def main():
    async for segment in fetch_events():
        print("Received segment:", segment)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
