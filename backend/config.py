import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    CHROMA_PATH = "./chroma_db"
    UPLOAD_DIR = "./tmp/uploads"
    DB_PATH = "./backend/db/aria.db"

settings = Settings()
