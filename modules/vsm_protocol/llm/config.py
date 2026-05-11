from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "qwen"
    / "qwen2.5-3b-instruct-q4_k_m.gguf"
)

PROMPTS_DIR = (
    BASE_DIR
    / "modules"
    / "vsm_protocol"
    / "prompts"
)

INTRO_PROMPT_PATH = PROMPTS_DIR / "protocol_intro_prompt.txt"
CONCLUSION_PROMPT_PATH = PROMPTS_DIR / "protocol_conclusion_prompt.txt"

LLM_CONFIG = {
    "n_ctx": 8192,
    "n_threads": 4,
    "temperature": 0.1,
    "max_tokens": 1800,
}