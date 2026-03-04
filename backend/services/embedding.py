import httpx
import config


async def get_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{config.OLLAMA_BASE_URL}/api/embed",
            json={"model": config.OLLAMA_EMBED_MODEL, "input": text},
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"][0]


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{config.OLLAMA_BASE_URL}/api/embed",
            json={"model": config.OLLAMA_EMBED_MODEL, "input": texts},
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"]
