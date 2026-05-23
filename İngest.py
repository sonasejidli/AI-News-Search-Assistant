import os
import time
import pandas as pd
import chromadb
from openai import OpenAI
from urllib.parse import urlparse
from tqdm import tqdm

from config import (
    OPENAI_API_KEY, CSV_PATH, CHROMA_PATH, COLLECTION_NAME,
    EMBEDDING_MODEL, BATCH_SIZE, CONTENT_LIMIT
)

PROGRESS_FILE = "embed_progress.txt"


def extract_source(url: str) -> str:
    try:
        netloc = urlparse(str(url)).netloc
        return netloc.replace("www.", "") if netloc else ""
    except Exception:
        return ""


def normalize_date(val) -> str:
    s = str(val).strip()
    if not s or s in ("nan", "None", ""):
        return ""
    return s[:10]


def prepare_data(df: pd.DataFrame):
    texts, ids, metadatas = [], [], []
    for i, row in df.iterrows():
        title = str(row.get("title", "")).strip()
        content = str(row.get("content", "")).strip()[:CONTENT_LIMIT]
        text = f"{title}\n\n{content}".strip()

        if not text:
            continue

        url = str(row.get("link", ""))
        texts.append(text)
        ids.append(f"doc_{i}")
        metadatas.append({
            "title": title[:500] if title else "Başlıqsız",
            "source": extract_source(url),
            "url": url,
            "published_at": normalize_date(row.get("created_at", "")),
            "category": str(row.get("category", "")),
        })
    return texts, ids, metadatas


def load_progress() -> int:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0


def save_progress(idx: int):
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(idx))


def main():
    print(f"📂 CSV oxunur: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"❌ CSV tapılmadı: {CSV_PATH}\n"
            f".env-də CSV_PATH-i dəyiş və ya faylı düzgün yerə qoy."
        )

    df = pd.read_csv(CSV_PATH)
    df = df.fillna("")
    print(f"✅ {len(df)} məqalə yükləndi")

    client = OpenAI(api_key=OPENAI_API_KEY)
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("🔧 Məlumatlar hazırlanır...")
    texts, ids, metadatas = prepare_data(df)
    print(f"✅ {len(texts)} məqalə embed olunmağa hazır")

    start_idx = load_progress()
    if start_idx > 0:
        print(f"⏩ Davam edirik: {start_idx}-dən")

    for start in tqdm(
        range(start_idx, len(texts), BATCH_SIZE),
        desc="Embedding",
        unit="batch"
    ):
        end = min(start + BATCH_SIZE, len(texts))
        batch_texts = texts[start:end]
        batch_ids = ids[start:end]
        batch_meta = metadatas[start:end]

        for attempt in range(3):
            try:
                resp = client.embeddings.create(
                    input=batch_texts,
                    model=EMBEDDING_MODEL,
                )
                embeddings = [d.embedding for d in resp.data]
                collection.add(
                    ids=batch_ids,
                    embeddings=embeddings,
                    documents=batch_texts,
                    metadatas=batch_meta,
                )
                save_progress(end)
                break
            except Exception as e:
                print(f"\n⚠️  Xəta (attempt {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    print(f"\n✅ TAMAMLANDI! Collection-da {collection.count()} məqalə var.")


if __name__ == "__main__":
    main()
