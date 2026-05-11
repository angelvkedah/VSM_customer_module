from llama_cpp import Llama
from pathlib import Path

model_path = Path("models/qwen/qwen2.5-3b-instruct-q4_k_m.gguf")

print("MODEL EXISTS:", model_path.exists())
print("MODEL PATH:", model_path.resolve())

llm = Llama(
    model_path=str(model_path),
    n_ctx=4096,
    n_threads=4,
    n_gpu_layers=0,
    verbose=False,
)

response = llm.create_chat_completion(
    messages=[
        {"role": "user", "content": "Напиши одно короткое предложение на русском."}
    ],
    max_tokens=100,
    temperature=0.1,
)

print(response["choices"][0]["message"]["content"])