import httpx

class HttpClientManager:
    _client: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient()
        return cls._client

    @classmethod
    async def close_client(cls):
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None