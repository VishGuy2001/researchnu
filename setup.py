from setuptools import setup, find_packages

setup(
    name="researchnu",
    version="1.0.0",
    description="Free agentic AI for researchers, founders and R&D teams",
    author="Vishnu Sekar",
    author_email="vishnusekar20@gmail.com",
    url="https://github.com/VishGuy2001/researchnu",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi",
        "uvicorn",
        "httpx",
        "pydantic",
        "langgraph",
        "langchain",
        "groq",
        "chromadb",
        "sentence-transformers",
        "rank-bm25",
        "python-dotenv",
        "slowapi",
        "streamlit",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)