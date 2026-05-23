import os
from dotenv import load_dotenv
 
load_dotenv()
 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CSV_PATH = os.getenv("CSV_PATH", "news_data.csv")
CHROMA_PATH = os.getenv("CHROMA_PATH", "embeddings/chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "news")
 
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
BATCH_SIZE = 100
CONTENT_LIMIT = 1500  # hər məqalədən neçə simvol embed olunsun
 
if not OPENAI_API_KEY:
    raise RuntimeError(
        "❌ OPENAI_API_KEY tapılmadı. .env faylını yoxla:\n"
        "  - Fayl adı dəqiq `.env` olmalıdır (env.txt YOX)\n"
        "  - İçində: OPENAI_API_KEY=sk-proj-...\n"
        "  - Boşluq və dırnaq olmamalıdır"
    )