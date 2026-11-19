from fastapi import Request


async def read_capped(request: Request, limit: int) -> bytes:
    received = bytearray()
    async for chunk in request.stream():
        received += chunk
        if len(received) > limit:
            return bytes(received[: limit + 1])
    return bytes(received)
