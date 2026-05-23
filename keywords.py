import re
from collections import Counter
from az_stopwords import AZ_STOPWORDS

WORD_PATTERN = re.compile(r"\b[A-Za-zƏəĞğİıÖöÜüÇçŞşı]{4,}\b", re.UNICODE)

CAPITAL_PHRASE = re.compile(
    r"\b[A-ZƏĞIÖÜÇŞ][a-zəğıöüçşi]+(?:\s+[A-ZƏĞIÖÜÇŞ][a-zəğıöüçşi]+){0,3}\b"
)

# Tanınmış təşkilat sonluqları / söz işarələri
ORG_SIGNALS = re.compile(
    r"\b(\w+\s*)?(Bank|SOCAR|ASC|MMC|SC|Ltd|Group|Holding|Agency|Fund|"
    r"Nazirliyi|Nazirlik|Komitəsi|Agentliyi|İdarəsi|Palatası|"
    r"University|Universitet|Institute|Institut|Hospital|Xəstəxana|"
    r"Airlines|Airways|Metro|Fondun|Fondları)\b",
    re.UNICODE | re.IGNORECASE,
)

# Yer adı siqnalları
LOCATION_SIGNALS = re.compile(
    r"\b(Bakı|Gəncə|Sumqayıt|Lənkəran|Mingəçevir|Naxçıvan|Şirvan|"
    r"Moskva|London|Paris|Ankara|İstanbul|Pekin|Vaşinqton|Brussel|"
    r"Azərbaycan|Türkiyə|Rusiya|ABŞ|Çin|Aİ|NATO|OPEC|"
    r"Avropa|Asiya|Afrika|Qafqaz|Xəzər)\b",
    re.UNICODE,
)


def _tokenize(text: str) -> list[str]:
    return WORD_PATTERN.findall(text or "")


def _is_meaningful(word: str) -> bool:
    w = word.lower().strip()
    if len(w) < 4:
        return False
    if w in AZ_STOPWORDS:
        return False
    if w.isdigit():
        return False
    return True


def _classify_entity(phrase: str) -> str:
    """Phrase-i kateqoriyaya ayır: org / location / other"""
    if ORG_SIGNALS.search(phrase):
        return "org"
    if LOCATION_SIGNALS.search(phrase):
        return "location"
    return "other"


def extract_keywords(
    articles: list[dict],
    top_n: int = 15,
    include_entities: bool = True,
) -> dict:
    """
    Returns:
        {
            "keywords": [(söz, count), ...],
            "orgs":     [(entity, count), ...],
            "locations": [(entity, count), ...],
            "entities": [(entity, count), ...],   # digərləri
            "total_articles": N
        }
    """
    if not articles:
        return {"keywords": [], "orgs": [], "locations": [], "entities": [], "total_articles": 0}

    word_counter = Counter()
    org_counter = Counter()
    location_counter = Counter()
    other_counter = Counter()

    for art in articles:
        title = art.get("title", "")
        content = art.get("content") or art.get("snippet", "")
        full_text = f"{title} {content}"

        for w in _tokenize(full_text):
            if _is_meaningful(w):
                word_counter[w.lower()] += 1

        if include_entities:
            for phrase in CAPITAL_PHRASE.findall(full_text):
                phrase = phrase.strip()
                if len(phrase.split()) == 1 and phrase.lower() in AZ_STOPWORDS:
                    continue
                if len(phrase) < 3:
                    continue
                cat = _classify_entity(phrase)
                if cat == "org":
                    org_counter[phrase] += 1
                elif cat == "location":
                    location_counter[phrase] += 1
                else:
                    other_counter[phrase] += 1

    return {
        "keywords": word_counter.most_common(top_n),
        "orgs": org_counter.most_common(top_n),
        "locations": location_counter.most_common(top_n),
        "entities": other_counter.most_common(top_n),
        "total_articles": len(articles),
    }


def format_keywords_text(result: dict, mode: str = "telegram") -> str:
    if not any([result["keywords"], result["orgs"], result["locations"], result["entities"]]):
        return "❌ Heç bir keyword tapılmadı."

    lines = [f"📊 *{result['total_articles']} məqalə üzərində analiz*\n"]

    if result["orgs"]:
        lines.append("*🏢 Təşkilatlar:*")
        for i, (ent, cnt) in enumerate(result["orgs"][:8], 1):
            lines.append(f"  {i}\\. {ent} — {cnt}")
        lines.append("")

    if result["locations"]:
        lines.append("*📍 Yerlər / Ölkələr:*")
        for i, (ent, cnt) in enumerate(result["locations"][:8], 1):
            lines.append(f"  {i}\\. {ent} — {cnt}")
        lines.append("")

    if result["entities"]:
        lines.append("*👤 Digər adlar:*")
        for i, (ent, cnt) in enumerate(result["entities"][:6], 1):
            lines.append(f"  {i}\\. {ent} — {cnt}")
        lines.append("")

    if result["keywords"]:
        lines.append("*🔑 Ən çox keçən sözlər:*")
        for i, (kw, cnt) in enumerate(result["keywords"][:10], 1):
            lines.append(f"  {i}\\. {kw} — {cnt}")

    return "\n".join(lines)


if __name__ == "__main__":
    sample = [
        {"title": "AccessBank yeni xidmət açdı",
         "content": "AccessBank müştəriləri üçün yeni kart xidməti təqdim etdi. Mərkəzi Bank bunu təsdiq etdi. Bakıda keçirilən tədbirə Maliyyə Nazirliyi nümayəndələri qatıldı."},
        {"title": "SOCAR-da yeni layihə",
         "content": "SOCAR Bakıda yeni neft emalı kompleksi tikəcək. Azərbaycan hökuməti layihəni dəstəkləyir."},
    ]
    result = extract_keywords(sample, top_n=10)
    print(format_keywords_text(result))
