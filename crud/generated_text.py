from sqlalchemy.orm import Session

from models.generated_text import GeneratedText


def create_generated_text(
    db: Session,
    text: str,
    theme: str = None,
    key_words: str = None,
    example_text: str = None,
    user_id: int = None,
):
    generated_text = GeneratedText(
        text=text,
        theme=theme,
        key_words=key_words,
        example_text=example_text,
        user_id=user_id,
    )
    db.add(generated_text)
    db.commit()
    db.refresh(generated_text)
    return generated_text


def get_generated_texts(db: Session, user_id: int = None, limit: int = 10):
    query = db.query(GeneratedText)
    if user_id:
        query = query.filter(GeneratedText.user_id == user_id)
    return query.order_by(GeneratedText.created_at.desc()).limit(limit).all()
