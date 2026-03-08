import os
import httpx
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def process_query_locally(query: str) -> str:
    # query never leaves the machine, ollama handles this
    # extracts intent so groq only sees a clean search prompt, not the raw idea
    r = httpx.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": f"Extract the core research intent from this query, keep it concise: {query}",
            "stream": False
        },
        timeout=120
    )
    # fallback to raw query if ollama isn't running
    return r.json().get("response", query)

def groq_complete(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    # groq only ever sees the processed prompt, not the original query
    # searches public sources, fast
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2048
    )
    return r.choices[0].message.content

def complete(prompt: str, use_local_query: bool = False) -> str:
    # privacy mode on = ollama processes first, groq never sees raw input
    # privacy mode off = groq handles everything, faster
    if use_local_query:
        prompt = process_query_locally(prompt)
    return groq_complete(prompt)