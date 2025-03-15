# routers/synonyms.py
import asyncio
from typing import List

import httpx
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from settings import YANDEX_API_KEY, get_logger

logger = get_logger(logger_name=__name__)

router = APIRouter()


class WordCountPair(BaseModel):
    word: str
    count: int


class SynonymsRequest(BaseModel):
    word_count_pairs: List[WordCountPair]


@router.post("/synonyms")
async def generate_synonyms(
    request: SynonymsRequest, current_user=Depends(get_current_user)
):
    try:
        async with httpx.AsyncClient() as client:
            # Запускаем параллельные задачи для поиска синонимов каждого слова
            tasks = [
                fetch_synonyms_for_word(client, pair.word, pair.count)
                for pair in request.word_count_pairs
            ]
            results = await asyncio.gather(*tasks)

        # Формируем ответ из результатов
        synonyms_result = [
            {"word": word, "synonyms": synonyms} for word, synonyms in results
        ]
        return synonyms_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def fetch_synonyms_for_word(client: httpx.AsyncClient, word: str, count: int):
    synonyms = await fetch_synonyms_from_yandex(client, word, count)
    return word, synonyms


async def fetch_synonyms_from_yandex(
    client: httpx.AsyncClient, word: str, count: int
) -> List[str]:
    url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup"
    params = {"key": YANDEX_API_KEY, "lang": "ru-ru", "text": word}
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Парсим синонимы из ответа API
        synonyms = []
        for definition in data.get("def", []):
            for translation in definition.get("tr", []):
                for synonym in translation.get("syn", []):
                    synonyms.append(synonym["text"])
                    if len(synonyms) >= count:
                        return synonyms
        return synonyms
    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка при обращении к Яндекс.Словарю: {e}")
        return []
