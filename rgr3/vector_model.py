"""Vector models for RGR No. 3, task 1.

The module implements the full preprocessing chain and both required models:

* one-hot encoding (binary vector of word presence);
* TF (term frequency) weighting.

It also contains helpers for the multiset intersection and cosine similarity.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import simplemma

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "rgr3" / "data"
TEXTS_DIR = DATA_DIR / "texts"

# Tokenization patterns are the same as in work No. 1 (see config.py):
# only Cyrillic letters for Russian and only Latin letters for English.
PATTERNS = {
    "ru": re.compile(r"[а-яё]+", re.IGNORECASE),
    "en": re.compile(r"[a-z]+", re.IGNORECASE),
}

# "20th" would otherwise leave the meaningless token "th" after tokenization.
ORDINAL_EN = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.IGNORECASE)

# Stop words are based on the function-word lists from RGR No. 2.  Before use
# they are also lemmatized, so that inflected forms are removed as well.
STOPWORDS_RU = [
    "в", "во", "на", "с", "со", "по", "к", "ко", "у", "за", "из", "от", "до",
    "для", "без", "под", "над", "при", "про", "через", "между", "перед",
    "около", "после", "кроме", "ради", "благодаря", "о", "об", "обо",
    "и", "а", "но", "да", "или", "либо", "если", "что", "чтобы", "когда",
    "пока", "потому", "так", "как", "тоже", "также", "ни", "то", "не", "же",
    "ли", "бы", "ведь", "вот", "вон", "даже", "уже", "еще", "только",
    "именно", "почти", "просто", "разве", "неужели",
    "я", "ты", "он", "она", "оно", "мы", "вы", "они", "меня", "тебя", "его",
    "ее", "её", "нас", "вас", "их", "мне", "тебе", "ему", "ей", "нам", "вам",
    "им", "себя", "себе", "собой",
    "этот", "эта", "это", "эти", "тот", "та", "те", "такой", "такая",
    "такое", "такие", "весь", "вся", "все", "свой", "мой", "моя", "моё",
    "мое", "мои", "твой", "твоё", "твое", "твои", "наш", "наша", "наше",
    "наши", "ваш", "ваша", "ваше", "ваши",
    "кто", "какой", "какая", "какое", "какие", "который", "которая",
    "которое", "которые", "чей", "чья", "чьё", "чье", "чьи", "где", "куда",
    "откуда", "почему", "зачем", "сколько",
    "быть", "был", "была", "было", "были", "будет", "буду", "будешь",
    "будем", "будете", "будут", "есть", "бытие",
    # Additional high-frequency function words and adverbs.
    "являться", "является", "являются", "являлся", "являлась", "являлись",
    "может", "могут", "можно", "нужно", "надо", "более", "менее", "самый",
    "самая", "самое", "самые", "самых", "каждый", "любой", "другой", "иной",
    "некоторый", "несколько", "много", "мало", "больше", "меньше", "очень",
    "весьма", "вполне", "довольно", "достаточно", "например", "однако",
    "причем", "причём", "поэтому", "затем", "тогда", "сейчас", "теперь",
    "здесь", "там", "тут",
]

STOPWORDS_EN = [
    "the", "a", "an", "of", "in", "to", "for", "with", "on", "at", "by",
    "from", "up", "about", "into", "over", "after", "beneath", "under",
    "above", "across", "along", "among", "around", "before", "behind",
    "below", "beside", "between", "beyond", "during", "except", "inside",
    "outside", "since", "through", "toward", "towards", "upon", "within",
    "without",
    "and", "or", "but", "nor", "so", "yet", "because", "although", "though",
    "if", "unless", "until", "while", "whereas", "whether", "as", "than",
    "that", "this", "these", "those",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "mine", "yours",
    "hers", "ours", "theirs", "myself", "yourself", "himself", "herself",
    "itself", "ourselves", "yourselves", "themselves",
    "who", "whom", "whose", "which", "what", "where", "when", "why", "how",
    "be", "am", "is", "are", "was", "were", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "done",
    "will", "would", "shall", "should", "can", "could", "may", "might",
    "must", "need", "dare", "ought",
    "not", "no", "yes", "too", "very", "just", "only", "also", "even",
    "well", "there", "here", "now", "then", "thus", "hence", "however",
    "therefore", "already", "still", "again", "ever", "never", "always",
    "often", "sometimes", "once", "soon", "almost", "quite", "rather",
    "perhaps", "maybe",
    # Quantifiers and other frequent function words.
    "all", "any", "both", "each", "every", "few", "many", "more", "most",
    "much", "several", "some", "such", "own", "same", "other", "another",
    "either", "neither",
    # Fragments left after tokenizing English contractions with [a-z]+.
    "don", "doesn", "didn", "isn", "aren", "wasn", "weren", "won", "wouldn",
    "couldn", "shouldn", "hasn", "haven", "hadn", "mustn", "needn", "shan",
    "mightn",
]

STOPWORDS = {"ru": STOPWORDS_RU, "en": STOPWORDS_EN}


def strip_accents(text: str) -> str:
    """Remove Russian stress marks without destroying the letters й and ё.

    In NFD the letter й is ``и`` + combining breve and ё is ``е`` + combining
    diaeresis, so removing *all* combining marks would corrupt normal Russian
    text.  Only the acute/grave stress marks are removed here.
    """
    text = unicodedata.normalize("NFD", text)
    text = text.replace("\u0301", "").replace("\u0300", "")
    return unicodedata.normalize("NFC", text)


def tokenize(text: str, lang: str) -> list[str]:
    """Split text into lower-case word tokens."""
    text = strip_accents(text).lower()
    if lang == "en":
        text = ORDINAL_EN.sub(" ", text)
    return PATTERNS[lang].findall(text)


def lemmatize_tokens(tokens: Iterable[str], lang: str) -> list[str]:
    """Normalize tokens with simplemma lemmatization."""
    # simplemma keeps the capital letter of proper nouns; for vector models the
    # case is irrelevant, so the result is lower-cased again.
    return [simplemma.lemmatize(token, lang=lang).lower() for token in tokens]


@lru_cache(maxsize=None)
def stopword_set(lang: str) -> frozenset[str]:
    """Return raw and lemmatized stop words for the language."""
    raw = {word.lower() for word in STOPWORDS[lang]}
    lemmatized = {simplemma.lemmatize(word, lang=lang).lower() for word in raw}
    return frozenset(raw | lemmatized)


def preprocess(text: str, lang: str) -> dict:
    """Tokenize, lemmatize and remove stop words."""
    raw_tokens = tokenize(text, lang)
    normalized_tokens = lemmatize_tokens(raw_tokens, lang)
    stops = stopword_set(lang)
    # Single letters left after tokenization are mostly artifacts (for example
    # the "t" in "don't"), so they are removed together with stop words.
    filtered_tokens = [
        token for token in normalized_tokens
        if token not in stops and len(token) >= 2
    ]
    return {
        "raw_tokens": raw_tokens,
        "normalized_tokens": normalized_tokens,
        "filtered_tokens": filtered_tokens,
        "raw_count": len(raw_tokens),
        "normalized_count": len(normalized_tokens),
        "filtered_count": len(filtered_tokens),
        "counter": Counter(filtered_tokens),
    }


def build_vocabulary(counters: Sequence[Counter]) -> list[str]:
    """Union vocabulary, sorted for reproducible vectors."""
    vocabulary: set[str] = set()
    for counter in counters:
        vocabulary.update(counter)
    return sorted(vocabulary)


def one_hot_matrix(counters: Sequence[Counter], vocabulary: Sequence[str]) -> np.ndarray:
    """Binary document-term matrix: 1 if the word occurs in the text, else 0."""
    matrix = np.zeros((len(counters), len(vocabulary)), dtype=np.int64)
    for row, counter in enumerate(counters):
        for col, word in enumerate(vocabulary):
            if word in counter:
                matrix[row, col] = 1
    return matrix


def tf_matrix(counters: Sequence[Counter], vocabulary: Sequence[str]) -> np.ndarray:
    """Term-frequency document-term matrix."""
    matrix = np.zeros((len(counters), len(vocabulary)), dtype=float)
    for row, counter in enumerate(counters):
        total = sum(counter.values())
        if total == 0:
            continue
        for col, word in enumerate(vocabulary):
            matrix[row, col] = counter.get(word, 0) / total
    return matrix


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    """Cosine of the angle between two vectors."""
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def multiset_intersection(left: Counter, right: Counter) -> Counter:
    """Multiset intersection: min(count_left, count_right) for every word."""
    return left & right


def top_counter(counter: Counter, limit: int = 15) -> list[dict]:
    return [
        {"word": word, "count": int(count)}
        for word, count in counter.most_common(limit)
    ]


def analyze_pair(
    lang: str,
    texts: Sequence[dict],
    top_n: int = 15,
) -> dict:
    """Run task 1 for one pair of texts of the same language."""
    documents = []
    for item in texts:
        path = ROOT / item["file"]
        text = path.read_text(encoding="utf-8")
        processed = preprocess(text, lang)
        documents.append({
            "key": item["key"],
            "title": item["title"],
            "file": item["file"],
            **processed,
        })

    counters = [doc["counter"] for doc in documents]
    vocabulary = build_vocabulary(counters)

    # One-hot encoding model.
    one_hot = one_hot_matrix(counters, vocabulary)
    one_hot_cosine = cosine_similarity(one_hot[0], one_hot[1])

    words_1 = set(counters[0])
    words_2 = set(counters[1])
    common_words = words_1 & words_2
    union_words = words_1 | words_2
    jaccard = len(common_words) / len(union_words) if union_words else 0.0

    # The task asks for the intersection of multisets.  For the binary
    # one-hot vectors this is the set of common words; for the original word
    # bags it is the Counter intersection (minimum of the two counts).
    multiset = multiset_intersection(counters[0], counters[1])
    multiset_size = sum(multiset.values())
    common_word_rows = [
        {
            "word": word,
            "count_text_1": int(counters[0].get(word, 0)),
            "count_text_2": int(counters[1].get(word, 0)),
            "min_count": int(multiset.get(word, 0)),
        }
        for word in sorted(
            common_words,
            key=lambda word: (-multiset.get(word, 0), word),
        )
    ]

    # TF model.
    tf = tf_matrix(counters, vocabulary)
    tf_cosine = cosine_similarity(tf[0], tf[1])

    return {
        "lang": lang,
        "texts": [
            {
                "key": doc["key"],
                "title": doc["title"],
                "file": doc["file"],
                "raw_tokens": doc["raw_count"],
                "raw_unique_tokens": len(set(doc["raw_tokens"])),
                "normalized_tokens": doc["normalized_count"],
                "normalized_unique_tokens": len(set(doc["normalized_tokens"])),
                "tokens_after_stopwords": doc["filtered_count"],
                "unique_tokens": len(doc["counter"]),
                "top_words": top_counter(doc["counter"], top_n),
            }
            for doc in documents
        ],
        "one_hot": {
            "vocabulary_size": len(vocabulary),
            "ones_in_matrix": int(one_hot.sum()),
            "common_unique_words": len(common_words),
            "union_unique_words": len(union_words),
            "jaccard_similarity": jaccard,
            "cosine_similarity": one_hot_cosine,
            "multiset_intersection_size": multiset_size,
            "common_words": common_word_rows,
        },
        "tf": {
            "vocabulary_size": len(vocabulary),
            "cosine_similarity": tf_cosine,
            "top_terms": [
                {
                    "key": doc["key"],
                    "title": doc["title"],
                    "terms": [
                        {"word": word, "tf": float(value)}
                        for word, value in sorted(
                            zip(vocabulary, tf[row]),
                            key=lambda pair: pair[1],
                            reverse=True,
                        )[:top_n]
                    ],
                }
                for row, doc in enumerate(documents)
            ],
        },
    }


def main() -> None:
    metadata = json.loads((DATA_DIR / "texts_metadata.json").read_text(encoding="utf-8"))
    results = {
        lang: analyze_pair(lang, items)
        for lang, items in metadata.items()
    }

    (DATA_DIR / "task1_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Compact table for the report.
    import csv

    with (DATA_DIR / "task1_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "language",
            "text_1",
            "text_2",
            "tokens_1",
            "tokens_2",
            "unique_1",
            "unique_2",
            "common_unique",
            "multiset_intersection",
            "jaccard",
            "cosine_one_hot",
            "cosine_tf",
        ])
        for lang, result in results.items():
            first, second = result["texts"]
            writer.writerow([
                lang,
                first["title"],
                second["title"],
                first["tokens_after_stopwords"],
                second["tokens_after_stopwords"],
                first["unique_tokens"],
                second["unique_tokens"],
                result["one_hot"]["common_unique_words"],
                result["one_hot"]["multiset_intersection_size"],
                f"{result['one_hot']['jaccard_similarity']:.6f}",
                f"{result['one_hot']['cosine_similarity']:.6f}",
                f"{result['tf']['cosine_similarity']:.6f}",
            ])

    for lang, result in results.items():
        first, second = result["texts"]
        print(f"[{lang}] {first['title']} / {second['title']}")
        print(f"  tokens after stop words: {first['tokens_after_stopwords']:,} / {second['tokens_after_stopwords']:,}")
        print(f"  unique words: {first['unique_tokens']:,} / {second['unique_tokens']:,}")
        print(f"  common unique words: {result['one_hot']['common_unique_words']:,}")
        print(f"  multiset intersection: {result['one_hot']['multiset_intersection_size']:,}")
        print(f"  Jaccard: {result['one_hot']['jaccard_similarity']:.4f}")
        print(f"  cosine (one-hot): {result['one_hot']['cosine_similarity']:.4f}")
        print(f"  cosine (TF): {result['tf']['cosine_similarity']:.4f}")
        print()


if __name__ == "__main__":
    main()
