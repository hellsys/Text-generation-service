from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from db import Base


class GeneratedText(Base):
    __tablename__ = "generated_texts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    text = Column(Text, nullable=False)
    theme = Column(String, index=True, nullable=True)
    key_words = Column(String, nullable=True)
    example_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
