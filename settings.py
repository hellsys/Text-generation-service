import logging
import os

from dotenv import load_dotenv

load_dotenv(override=True)

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost/postgres"
)


THEME_TEXT = """Ты должен сгенерировать текст по следующей теме: {theme}.
Текст должен содержать не более {max_length} {max_length_type}."""

KEY_WORDS_TEXT = """Ты должен сгенерировать текст по следующим ключевым словам: {key_words}.
Текст должен содержать не более {max_length} {max_length_type}."""

EXAMPLE_TEXT = """Ты должен сгенерировать текст, похожий на следующий пример: {example_text}.
Текст должен содержать не более {max_length} {max_length_type}."""


def get_logger(level=logging.INFO, logger_name="default logger") -> logging.Logger:
    logging.basicConfig(level=level)

    handler = logging.FileHandler("myapp.log")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger
