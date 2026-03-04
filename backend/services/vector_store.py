import os
import lancedb
import pyarrow as pa
import config

_db = None
TABLE_NAME = "hr_regulations"


def get_db() -> lancedb.DBConnection:
    global _db
    if _db is None:
        os.makedirs(config.LANCEDB_PATH, exist_ok=True)
        _db = lancedb.connect(config.LANCEDB_PATH)
    return _db


def create_table(data: list[dict]):
    """Create or overwrite the vector table with chunked documents."""
    db = get_db()
    if TABLE_NAME in db.table_names():
        db.drop_table(TABLE_NAME)
    db.create_table(TABLE_NAME, data=data)


def search(query_vector: list[float], top_k: int = None) -> list[dict]:
    """Search for similar document chunks."""
    if top_k is None:
        top_k = config.VECTOR_TOP_K
    db = get_db()
    if TABLE_NAME not in db.table_names():
        return []
    table = db.open_table(TABLE_NAME)
    results = (
        table.search(query_vector)
        .limit(top_k)
        .to_list()
    )
    return results


# Korean suffixes to strip (sorted longest first at runtime)
_SUFFIXES = [
    # Noun particles
    "은", "는", "이", "가", "을", "를", "에", "의", "도", "로", "으로",
    "에서", "부터", "까지", "한테", "에게", "와", "과", "하고", "이나", "나",
    "에서는", "에서도", "으로는", "이랑", "랑",
    # Verb/adjective endings
    "하면", "되면", "받으면", "하려면", "하면서",
    "해야돼", "해야해", "해야하나", "해야되",
    "하나요", "한가요", "할까요", "할까", "할수있어", "할수있나",
    "줘", "줘요", "주나", "주니", "주세요", "주나요",
    "인가", "인가요", "인지", "인데", "이야", "이에요",
    "되나", "되나요", "돼", "돼요", "되?", "됨?",
    "거든", "잖아", "네요", "나요", "던가",
    "어떻게돼", "어떻게되", "어떻게해",
    "입어도돼", "입어도되", "입어야해", "입어야돼",
    "신어도돼", "신어도되", "신어야해",
    "들어줘", "들어줘?", "들어주나",
    "쓸수있어", "쓸수있나", "쓸수있어?",
    "얼마야", "얼마야?", "얼마나", "얼마줘",
    "몇살이야", "몇살",
    "뭐야", "뭐야?", "뭐해야돼",
    "어떻게", "어떡해",
    "하고싶어", "하고싶은데",
    "있어", "있어?", "있나", "있나요", "있을까",
    "없어", "없어?", "없나",
    "해줘", "해줘요", "해주나", "해줄수있어",
    "시켜줘", "시켜줘?",
    "알려줘", "알려줘요", "알려주세요",
    "ㅠ", "ㅠㅠ", "??", "?",
]

# Synonyms cache: built from DB glossary aliases
_synonyms_cache: dict[str, list[str]] | None = None
_synonyms_cache_time: float = 0


def _load_synonyms() -> dict[str, list[str]]:
    """Build synonym map from glossary aliases in DuckDB.

    Each glossary entry has: term (formal) and aliases (comma-separated colloquial forms).
    We build: alias → [term] mapping so colloquial queries find formal document terms.
    Also: term → [aliases] so formal terms expand to related words.
    """
    global _synonyms_cache, _synonyms_cache_time
    import time
    now = time.time()
    # Cache for 60 seconds to avoid DB hits on every search
    if _synonyms_cache is not None and now - _synonyms_cache_time < 60:
        return _synonyms_cache

    from services.db import get_conn
    synonyms: dict[str, list[str]] = {}
    try:
        conn = get_conn()
        rows = conn.execute("SELECT term, aliases FROM glossary WHERE aliases != ''").fetchall()
        for term, aliases_str in rows:
            alias_list = [a.strip() for a in aliases_str.split(",") if a.strip()]
            # alias → term (colloquial → formal)
            for alias in alias_list:
                if alias not in synonyms:
                    synonyms[alias] = []
                if term not in synonyms[alias]:
                    synonyms[alias].append(term)
            # term → aliases (formal → colloquial, for broader matching)
            if alias_list:
                if term not in synonyms:
                    synonyms[term] = []
                for alias in alias_list:
                    if alias not in synonyms[term]:
                        synonyms[term].append(alias)
    except Exception:
        pass

    _synonyms_cache = synonyms
    _synonyms_cache_time = now
    return synonyms

def invalidate_synonyms_cache():
    """Clear the synonyms cache so next search reloads from DB."""
    global _synonyms_cache
    _synonyms_cache = None


_SORTED_SUFFIXES = sorted(_SUFFIXES, key=len, reverse=True)


def _stem_word(word: str) -> list[str]:
    """Strip Korean suffixes from a word to extract stems."""
    stems = {word}
    for s in _SORTED_SUFFIXES:
        if word.endswith(s) and len(word) - len(s) >= 2:
            stems.add(word[: -len(s)])
    return list(stems)


def keyword_search(query: str, top_k: int = None) -> list[dict]:
    """Keyword-based search with Korean stem matching and synonyms."""
    if top_k is None:
        top_k = config.VECTOR_TOP_K
    db = get_db()
    if TABLE_NAME not in db.table_names():
        return []
    table = db.open_table(TABLE_NAME)

    import re
    words = re.findall(r"[\w]+", query)

    # Build search terms from stems + synonyms
    synonyms = _load_synonyms()
    search_terms = set()
    for w in words:
        # Check 1-char words in synonyms (e.g., "옷")
        if len(w) == 1 and w in synonyms:
            search_terms.update(synonyms[w])
            continue
        if len(w) < 2:
            continue

        stems = _stem_word(w)
        for stem in stems:
            search_terms.add(stem)
            # Add synonyms for the stem
            if stem in synonyms:
                search_terms.update(synonyms[stem])
            # Check if stem is a prefix of a synonym key or vice versa
            for syn_key, syn_vals in synonyms.items():
                if len(stem) >= 2 and len(syn_key) >= 2:
                    if stem.startswith(syn_key) or syn_key.startswith(stem):
                        search_terms.update(syn_vals)
                        search_terms.add(syn_key)

    # Filter: minimum 2 chars
    search_terms = {t for t in search_terms if len(t) >= 2}
    if not search_terms:
        return []

    all_rows = table.search([0.0] * config.EMBED_DIM).limit(500).to_list()
    scored = []
    for row in all_rows:
        text = row.get("text", "")
        section = row.get("section", "")
        best_len = 0
        match_count = 0
        section_bonus = 0
        for term in search_terms:
            if term in text:
                match_count += 1
                best_len = max(best_len, len(term))
                # Bonus if term appears in section title (more relevant)
                if term in section:
                    section_bonus += len(term) * 5
        if match_count > 0 and best_len >= 2:
            row["_keyword_score"] = best_len * 10 + match_count + section_bonus
            scored.append(row)

    scored.sort(key=lambda x: x["_keyword_score"], reverse=True)
    return scored[:top_k]
