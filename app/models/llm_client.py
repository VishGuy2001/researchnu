import os
from groq import Groq

# groq is fast and free, default choice
_groq = None

def get_groq():
    global _groq
    if not _groq:
        _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq

def groq_chat(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    try:
        r = get_groq().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3,
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"LLM error: {e}"

def local_chat(prompt: str) -> str:
    # ollama local — privacy mode, query never leaves server
    try:
        import ollama
        r = ollama.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}]
        )
        return r["message"]["content"]
    except Exception as e:
        print(f"ollama failed, falling back to groq: {e}")
        return groq_chat(prompt)