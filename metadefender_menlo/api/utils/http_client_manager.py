import httpx
from metadefender_menlo.api.config import Config

class HttpClientManager:
    _client: httpx.AsyncClient | None = None
    _limits: httpx.Limits | None = None

    @classmethod
    def _build_limits(cls) -> httpx.Limits:
        cfg = Config.get_all() or {}
        limits_cfg = cfg.get('httpx_limits', {}) or {}
        if limits_cfg.get('enabled'):
            raw_max_conn = limits_cfg.get('max_connections', None)
            if raw_max_conn is None:
                return httpx.Limits()
            try:
                max_conn = int(raw_max_conn)
                return httpx.Limits(max_connections=max_conn)
            except (TypeError, ValueError):
                return httpx.Limits()
        return httpx.Limits()

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            if cls._limits is None:
                cls._limits = cls._build_limits()
            cls._client = httpx.AsyncClient(limits=cls._limits)
        return cls._client

    @classmethod
    async def close_client(cls):
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None