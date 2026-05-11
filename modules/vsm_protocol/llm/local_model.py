import os
import subprocess
import sys
import tempfile
from pathlib import Path


def generate_text(prompt: str) -> str:
    """
    Генерирует текст через отдельный Python-процесс.
    """

    worker_path = Path(__file__).resolve().parent / "llm_worker.py"

    project_root = Path(__file__).resolve().parents[3]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        prompt_path = temp_dir_path / "prompt.txt"
        output_path = temp_dir_path / "output.txt"

        prompt_path.write_text(prompt, encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        result = subprocess.run(
            [
                sys.executable,
                str(worker_path),
                str(prompt_path),
                str(output_path),
            ],
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Ошибка генерации текста локальной моделью:\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}"
            )

        if not output_path.exists():
            raise RuntimeError(
                "Модель завершила работу, но файл ответа не был создан."
            )

        return output_path.read_text(encoding="utf-8").strip()