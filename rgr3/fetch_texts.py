"""Fetch the two Russian and two English texts used in RGR No. 3.

The texts are taken from the same corpus as in work No. 1:
``wikimedia/wikipedia``, version ``20231101`` (see ``config.py``).
Only the four selected articles are written to ``rgr3/data/texts``.

Run from the repository root:

    .venv/bin/python rgr3/fetch_texts.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "rgr3" / "data"
TEXTS_DIR = DATA_DIR / "texts"

DATASET_NAME = "wikimedia/wikipedia"
VERSION = "20231101"

# Titles from the same Wikipedia dump that was used to build the frequency
# dictionaries in work No. 1.  The pairs are close in size (about 5.7-6.7k
# words per text).
TARGETS = {
    "ru": [
        ("ru_1", "Литва"),
        ("ru_2", "Кавказские Минеральные Воды"),
    ],
    "en": [
        ("en_1", "Anarchism"),
        ("en_2", "Ayn Rand"),
    ],
}


def main() -> None:
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    metadata: dict[str, list[dict]] = {}

    for lang, targets in TARGETS.items():
        wanted = {title: key for key, title in targets}
        found: dict[str, dict] = {}

        dataset = load_dataset(
            DATASET_NAME,
            name=f"{VERSION}.{lang}",
            split="train",
            streaming=True,
        )

        for article in dataset:
            title = article["title"]
            if title not in wanted:
                continue

            key = wanted[title]
            text = article["text"]
            path = TEXTS_DIR / f"{key}.txt"
            path.write_text(text, encoding="utf-8")

            found[key] = {
                "key": key,
                "lang": lang,
                "title": title,
                "id": article.get("id"),
                "url": article.get("url"),
                "file": str(path.relative_to(ROOT)),
                "approx_words": len(text.split()),
            }
            print(f"{lang}: {key} <- {title!r} ({len(text.split()):,} words)")

            if len(found) == len(targets):
                break

        missing = set(wanted.values()) - set(found)
        if missing:
            raise RuntimeError(f"Articles not found for {lang}: {sorted(missing)}")

        metadata[lang] = [found[key] for key, _ in targets]

    (DATA_DIR / "texts_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # HuggingFace streaming may keep background threads alive; exit explicitly
    # after all files have been flushed.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
