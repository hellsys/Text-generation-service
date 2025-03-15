# routers/generate.py
from typing import List

from crud.generated_text import create_generated_text, get_generated_texts
from dependencies.auth import get_current_user
from dependencies.database import get_db
from fastapi import APIRouter, Depends
from models.auth import User
from models.model import TextGenerationModel
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()
model_instance = TextGenerationModel()


class GenerateRequest(BaseModel):
    num_samples: int = 1
    max_length: int | None = None
    max_length_type: str
    temperature: float
    theme: str | None = None
    key_words: List[List[str]] | None = None
    example_text: str | None = None


@router.post("/generate")
async def generate_text(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Генерация текста
    generated_texts = await model_instance.generate_text(
        num_samples=request.num_samples,
        max_length=request.max_length,
        max_length_type=request.max_length_type,
        theme=request.theme,
        key_words=request.key_words,
        example_text=request.example_text,
        temperature=request.temperature,
    )

    # Сохранение сгенерированных текстов в базе данных
    saved_texts = []
    for text in generated_texts:
        saved_text = create_generated_text(
            db=db,
            text=text,
            theme=request.theme,
            key_words=", ".join(
                [", ".join(key_words_group) for key_words_group in request.key_words]
            )
            if request.key_words
            else None,
            example_text=request.example_text,
            user_id=current_user.id if current_user else None,
        )
        saved_texts.append(saved_text)

    return {"generated_texts": [t.text for t in saved_texts]}


@router.get("/generated_texts")
def get_texts(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    texts = get_generated_texts(db=db, user_id=current_user.id, limit=limit)
    return {
        "generated_texts": [
            {"id": t.id, "text": t.text, "theme": t.theme, "created_at": t.created_at}
            for t in texts
        ]
    }
