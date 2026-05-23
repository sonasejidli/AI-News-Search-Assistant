"""
Mövcud ChromaDB collection-undakı metadata-nı CSV-dən yenilə.
link → url, created_at → published_at, domain → source
Həm "doc_N" həm də plain "N" ID formatlarını dəstəkləyir.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import chromadb
from urllib.parse import urlparse
from tqdm import tqdm

from config import CSV_PATH, CHROMA_PATH, COLLECTION_NAME

BATCH = 500


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


def build_meta(row) -> dict:
    title = str(row.get("title", "")).strip()
    url = str(row.get("link", ""))
    return {
        "title": title[:500] if title else "Başlıqsız",
        "source": extract_source(url),
        "url": url,
        "published_at": normalize_date(row.get("created_at", "")),
        "category": str(row.get("category", "")),
    }


def main():
    print(f"📂 CSV oxunur: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    df = df.fillna("")
    print(f"✅ {len(df)} sətir yükləndi. Sütunlar: {list(df.columns)}")

    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    col = chroma.get_collection(COLLECTION_NAME)
    print(f"📦 ChromaDB-də {col.count()} məqalə var")

    existing = col.get(include=[])
    existing_ids = set(existing["ids"])
    print(f"🔑 {len(existing_ids)} mövcud ID tapıldı")

    ids_batch, metas_batch = [], []
    updated = 0

    for i, row in tqdm(df.iterrows(), total=len(df), desc="Metadata yenilənir"):
        meta = build_meta(row)

        # "doc_N" formatı
        doc_id = f"doc_{i}"
        if doc_id in existing_ids:
            ids_batch.append(doc_id)
            metas_batch.append(meta)

        # Plain "N" formatı (köhnə ingest)
        plain_id = str(i)
        if plain_id in existing_ids:
            ids_batch.append(plain_id)
            metas_batch.append(meta)

        if len(ids_batch) >= BATCH:
            col.update(ids=ids_batch, metadatas=metas_batch)
            updated += len(ids_batch)
            ids_batch, metas_batch = [], []

    if ids_batch:
        col.update(ids=ids_batch, metadatas=metas_batch)
        updated += len(ids_batch)

    print(f"\n✅ {updated} ID-nin metadata-sı yeniləndi!")

    # Yoxlama
    print("\nNümunə (doc_ formatı):")
    s1 = col.get(ids=["doc_0", "doc_100"], include=["metadatas"])
    for id_, m in zip(s1["ids"], s1["metadatas"]):
        print(f"  {id_}: source={m['source']!r}  pub={m['published_at']!r}")

    print("\nNümunə (plain formatı):")
    s2 = col.get(ids=["2820", "5517"], include=["metadatas"])
    for id_, m in zip(s2["ids"], s2["metadatas"]):
        print(f"  {id_}: source={m['source']!r}  pub={m['published_at']!r}")


if __name__ == "__main__":
    main()
