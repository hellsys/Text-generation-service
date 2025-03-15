# models/model.py
import asyncio
import itertools
import os
import re
from pathlib import Path
from typing import List, Optional

import openai
import torch
from huggingface_hub import snapshot_download
from openai import AsyncOpenAI
from settings import (
    EXAMPLE_TEXT,
    HUGGINGFACE_TOKEN,
    KEY_WORDS_TEXT,
    MODEL_PROVIDER,
    OPENAI_API_KEY,
    THEME_TEXT,
    get_logger,
)
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = get_logger(logger_name=__name__)


class TextGenerationModel:
    def __init__(self):
        # Загрузка переменных окружения

        self.model_provider = MODEL_PROVIDER.lower()

        if self.model_provider == "mistral":
            self._initialize_mistral()
        elif self.model_provider == "openai":
            self._initialize_openai()
        else:
            raise ValueError(
                "Неверное значение переменной MODEL_PROVIDER. Допустимые значения: 'mistral', 'openai'."
            )

    def _initialize_mistral(self):
        # Инициализация модели Mistral
        logger.info("Инициализация модели Mistral.")
        self.hf_token = HUGGINGFACE_TOKEN
        if not self.hf_token:
            raise ValueError("Переменная окружения HUGGINGFACE_TOKEN не установлена.")

        self.model_name = "mistralai/Mistral-7B-v0.1"
        self.cache_dir = os.path.join(os.getcwd(), "models", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Проверяем наличие модели
        model_path = Path(self.cache_dir) / (
            "models--" + self.model_name.replace("/", "--")
        )
        if not model_path.exists():
            logger.info("Модель не найдена локально. Начинается загрузка...")
            self.download_model()
        else:
            logger.info("Модель найдена локально. Загрузка из кэша.")

        # Автоматический выбор устройства
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            logger.info("Используется Apple GPU (MPS).")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            logger.info(f"Используется NVIDIA GPU: {torch.cuda.get_device_name(0)}.")
        else:
            self.device = torch.device("cpu")
            logger.info("Используется CPU.")

        # Загрузка токенизатора и модели из локального кэша с использованием токена
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, cache_dir=self.cache_dir, token=self.hf_token
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            token=self.hf_token,
            torch_dtype=torch.float16 if self.device.type != "mps" else torch.float32,
            device_map=None,
        ).to(self.device)

    def _initialize_openai(self):
        # Инициализация OpenAI API
        logger.info("Инициализация OpenAI API.")
        self.openai_api_key = OPENAI_API_KEY
        if not self.openai_api_key:
            raise ValueError("Переменная окружения OPENAI_API_KEY не установлена.")
        openai.api_key = self.openai_api_key
        self.model_name = "gpt-4o"  # Вы можете изменить модель на нужную
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)

    def download_model(self):
        # Загрузка модели Mistral с использованием токена
        try:
            snapshot_download(
                repo_id=self.model_name,
                cache_dir=self.cache_dir,
                use_auth_token=self.hf_token,
                resume_download=True,
                local_dir_use_symlinks=False,
            )
            logger.info("Модель успешно загружена.")
        except Exception as e:
            logger.info(f"Ошибка при загрузке модели: {e}")
            raise e

    async def generate_text(
        self,
        num_samples,
        max_length,
        max_length_type,
        theme,
        key_words,
        example_text,
        temperature,
    ):
        if self.model_provider == "mistral":
            return await self._generate_with_mistral(
                num_samples,
                max_length,
                max_length_type,
                theme,
                key_words,
                example_text,
                temperature,
            )
        elif self.model_provider == "openai":
            return await self._generate_with_openai(
                num_samples,
                max_length,
                max_length_type,
                theme,
                key_words,
                example_text,
                temperature,
            )

    async def _generate_with_mistral(
        self,
        num_samples: int = 1,
        max_length: Optional[int] = None,
        max_length_type: Optional[str] = None,
        theme: Optional[str] = None,
        key_words: Optional[List[str]] = None,
        example_text: Optional[str] = None,
        temperature: Optional[float] = 1,
    ) -> List[str]:
        tasks = []
        for _ in range(num_samples):
            tasks.append(
                asyncio.to_thread(
                    self._generate_with_mistral_sync,
                    max_length,
                    max_length_type,
                    theme,
                    key_words,
                    example_text,
                    temperature,
                )
            )
        generated_texts = await asyncio.gather(*tasks)
        return generated_texts

    def _generate_with_mistral_sync(
        self,
        max_length: Optional[int],
        max_length_type: Optional[str],
        theme: Optional[str],
        key_words: Optional[List[str]],
        example_text: Optional[str],
        temperature: Optional[float],
    ) -> str:
        # Формируем промпт
        if theme:
            request_text = THEME_TEXT.format(
                theme=theme, max_length=max_length, max_length_type=max_length_type
            )
        elif key_words:
            key_words_str = ", ".join(key_words)
            request_text = KEY_WORDS_TEXT.format(
                key_words=key_words_str,
                max_length=max_length,
                max_length_type=max_length_type,
            )
        elif example_text:
            request_text = EXAMPLE_TEXT.format(
                example_text=example_text,
                max_length=max_length,
                max_length_type=max_length_type,
            )
        else:
            request_text = (
                "Сгенерируйте текст по заданной теме с указанными ограничениями."
            )

        # Определяем max_tokens
        max_tokens = self._determine_max_tokens(max_length, max_length_type)

        inputs = self.tokenizer(request_text, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_length=max_tokens,
            num_return_sequences=1,
            do_sample=True,
            temperature=temperature,
        )
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Строгий контроль длины текста
        generated_text = self._enforce_length_constraints(
            generated_text, max_length, max_length_type
        )

        return generated_text

    async def _generate_with_openai(
        self,
        num_samples: int = 1,
        max_length: Optional[int] = None,
        max_length_type: Optional[str] = None,
        theme: Optional[str] = None,
        key_words: Optional[List[List[str]]] = None,  # список групп синонимов
        example_text: Optional[str] = None,
        temperature: Optional[float] = 1,
    ) -> List[str]:
        tasks = []

        if key_words:
            all_combinations = list(itertools.product(*key_words))
        else:
            all_combinations = None

        for i in range(num_samples):
            if all_combinations:
                combination = all_combinations[i % len(all_combinations)]
                selected_keywords_str = ", ".join(combination)
            else:
                selected_keywords_str = None

            tasks.append(
                self._call_openai_api(
                    max_length,
                    max_length_type,
                    theme,
                    key_words=selected_keywords_str,
                    example_text=example_text,
                    temperature=temperature,
                )
            )
        generated_texts = await asyncio.gather(*tasks)
        return generated_texts

    async def _call_openai_api(
        self,
        max_length: Optional[int],
        max_length_type: Optional[str],
        theme: Optional[str],
        key_words: Optional[str],
        example_text: Optional[str],
        temperature: Optional[float],
    ) -> str:
        # Формируем промпт на основе переданных параметров
        if theme:
            request_text = THEME_TEXT.format(
                theme=theme, max_length=max_length, max_length_type=max_length_type
            )
        elif key_words:
            request_text = KEY_WORDS_TEXT.format(
                key_words=key_words,
                max_length=max_length,
                max_length_type=max_length_type,
            )
        elif example_text:
            request_text = EXAMPLE_TEXT.format(
                example_text=example_text,
                max_length=max_length,
                max_length_type=max_length_type,
            )
        else:
            request_text = (
                "Сгенерируйте текст по заданной теме с указанными ограничениями."
            )

        # Определяем max_tokens на основе max_length_type
        max_tokens = self._determine_max_tokens(max_length, max_length_type)

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": request_text}],
                n=1,
                stop=None,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            generated_text = response.choices[0].message.content

            # Строгий контроль длины текста
            generated_text = self._enforce_length_constraints(
                generated_text, max_length, max_length_type
            )

            return generated_text
        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API: {e}")
            raise e

    def _determine_max_tokens(
        self, max_length: Optional[int], max_length_type: Optional[str]
    ) -> Optional[int]:
        if not max_length or not max_length_type:
            return None  # Использовать значение по умолчанию

        if max_length_type == "tokens":
            return max_length
        elif max_length_type == "words":
            # Приблизительное преобразование слов в токены
            return int(max_length * 1.7)  # Коэффициент может варьироваться
        elif max_length_type == "symbols":
            return int(max_length / 4)  # Приблизительно 4 символа на токен
        elif max_length_type == "sentences":
            return (
                max_length * 30
            )  # Предполагаем, что в одном предложении около 20 токенов
        else:
            logger.warning(
                f"Неизвестный тип ограничения длины: {max_length_type}. Используется значение по умолчанию."
            )
            return 100  # Значение по умолчанию

    def _enforce_length_constraints(
        self, text: str, max_length: Optional[int], max_length_type: Optional[str]
    ) -> str:
        if not max_length or not max_length_type:
            return text  # Нет ограничений

        if max_length_type == "symbols":
            if len(text) > max_length:
                text = text[:max_length]
        elif max_length_type == "words":
            words = text.split()
            if len(words) > max_length:
                text = " ".join(words[:max_length])
        elif max_length_type == "sentences":
            sentences = re.split(r"(?<=[.!?]) +", text)
            if len(sentences) > max_length:
                text = " ".join(sentences[:max_length])
        elif max_length_type == "tokens":
            # Точное ограничение по токенам, уже учтено через max_tokens
            pass
        else:
            logger.warning(
                f"Неизвестный тип ограничения длины: {max_length_type}. Ограничение не применяется."
            )

        return text
