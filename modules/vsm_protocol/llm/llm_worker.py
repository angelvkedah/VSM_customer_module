import re
import sys
from pathlib import Path

from llama_cpp import Llama

from modules.vsm_protocol.llm.config import MODEL_PATH


def has_chinese_chars(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def main():
    prompt_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    prompt = prompt_path.read_text(encoding="utf-8")

    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=8192,
        n_threads=4,
        n_gpu_layers=0,
        verbose=False,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ты русскоязычный инженер-аналитик диагностических сообщений. "
                "Отвечай строго на русском языке. "
                "Запрещено использовать китайский, английский или смешанный язык. "
                "Не добавляй факты, которых нет во входных данных."
            ),
        },
        {
            "role": "user",
            "content": (
                "Ответ должен быть полностью на русском языке.\n"
                "Не используй китайские иероглифы.\n"
                "Не используй английские слова, если они не являются частью технического кода.\n\n"
                + prompt
            ),
        },
    ]

    response = llm.create_chat_completion(
        messages=messages,
        temperature=0.01,
        max_tokens=3500,
        top_p=0.7,
        repeat_penalty=1.25,
    )

    text = response["choices"][0]["message"]["content"].strip()

    # Если модель ушла в китайский
    if has_chinese_chars(text):
        retry_prompt = (
            "Перепиши следующий текст полностью на русском языке. "
            "Удалить все китайские иероглифы. "
            "Сохранить только факты из текста.\n\n"
            f"{text}"
        )

        retry_response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "Ты переводишь и нормализуешь текст строго на русский язык.",
                },
                {
                    "role": "user",
                    "content": retry_prompt,
                },
            ],
            temperature=0.01,
            max_tokens=3500,
            top_p=0.7,
            repeat_penalty=1.25,
        )

        text = retry_response["choices"][0]["message"]["content"].strip()

    output_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()