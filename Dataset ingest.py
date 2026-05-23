import os
import sys
from dotenv import load_dotenv
 
print("=" * 60)
print("🔧 SETUP YOXLAMASI")
print("=" * 60)
 
# 1. .env yoxla
print("\n1. .env faylı...")
if not os.path.exists(".env"):
    print("   ❌ .env tapılmadı! Yarat və içinə yaz:")
    print("      OPENAI_API_KEY=sk-proj-...")
    print("      TELEGRAM_BOT_TOKEN=...")
    sys.exit(1)
print("   ✅ .env tapıldı")
 
load_dotenv()
 
# 2. Key-ləri yoxla
print("\n2. API key-lər...")
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("   ❌ OPENAI_API_KEY .env-də yoxdur (və ya boşdur)")
    print("   .env faylını VS Code-da aç, daxilini yoxla:")
    print("   - Fayl adı dəqiq `.env` olmalıdır (`env.txt` YOX)")
    print("   - Format: OPENAI_API_KEY=sk-proj-...")
    print("   - Bərabərlik ətrafında BOŞLUQ olmamalıdır")
    print("   - DIRNAQ olmamalıdır")
    sys.exit(1)
print(f"   ✅ OPENAI_API_KEY: {openai_key[:15]}... (uzunluq: {len(openai_key)})")
 
tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not tg_token:
    print("   ⚠️  TELEGRAM_BOT_TOKEN yoxdur (yalnız botu işə salanda lazımdır)")
else:
    print(f"   ✅ TELEGRAM_BOT_TOKEN: {tg_token[:10]}...")
 
# 3. CSV yoxla
print("\n3. Dataset...")
csv_path = os.getenv("CSV_PATH", "news_data.csv")
if not os.path.exists(csv_path):
    print(f"   ⚠️  CSV tapılmadı: {csv_path}")
    print("      .env-də CSV_PATH-i düzəlt, və ya CSV-ni layihə qovluğuna at.")
else:
    import pandas as pd
    try:
        df = pd.read_csv(csv_path, nrows=5)
        print(f"   ✅ CSV oxundu: {csv_path}")
        print(f"      Sütunlar: {list(df.columns)}")
    except Exception as e:
        print(f"   ❌ CSV oxunmur: {e}")
 
# 4. Modulları import et
print("\n4. Python paketləri...")
required = ["openai", "chromadb", "pandas", "tqdm", "telegram", "streamlit"]
missing = []
for pkg in required:
    try:
        __import__(pkg)
        print(f"   ✅ {pkg}")
    except ImportError:
        print(f"   ❌ {pkg} quraşdırılmayıb")
        missing.append(pkg)
 
if missing:
    print(f"\n   Quraşdırmaq üçün: pip install {' '.join(missing)}")
    sys.exit(1)
 
# 5. OpenAI testi
print("\n5. OpenAI API testi...")
try:
    from openai import OpenAI
    client = OpenAI(api_key=openai_key)
    resp = client.embeddings.create(
        input="test",
        model="text-embedding-3-small",
    )
    print(f"   ✅ OpenAI işləyir (embedding ölçüsü: {len(resp.data[0].embedding)})")
except Exception as e:
    print(f"   ❌ OpenAI xətası: {e}")
    print("      API key-i yoxla, kreditin var?")
    sys.exit(1)
 
# 6. ChromaDB
print("\n6. ChromaDB...")
try:
    import chromadb
    chroma_path = os.getenv("CHROMA_PATH", "embeddings/chroma_db")
    chroma = chromadb.PersistentClient(path=chroma_path)
    col = chroma.get_or_create_collection("news")
    count = col.count()
    if count == 0:
        print(f"   ⚠️  Collection boşdur. İlk dəfə üçün: python ingest.py")
    else:
        print(f"   ✅ Collection-da {count} məqalə var")
except Exception as e:
    print(f"   ❌ ChromaDB xətası: {e}")
 
print("\n" + "=" * 60)
print("✅ SETUP YOXLAMASI BİTDİ")
print("=" * 60)
print("\nNövbəti addımlar:")
print("  1. python ingest.py        # əgər collection boşdursa")
print("  2. python bot.py           # Telegram bot")
print("  3. streamlit run app.py    # Web frontend")