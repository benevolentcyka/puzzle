"""Reproduce the duplicate-paragraph ID check on saved Wattpad API text."""
import hashlib
import html
import json
import re
from pathlib import Path

here = Path(__file__).resolve().parent
result = {}
for part_id in [720888559, 720895205]:
    source = (here / f"wattpad-api-{part_id}.txt").read_text(encoding="utf-8")
    paragraphs = []
    for paragraph_id, raw in re.findall(r'<p data-p-id="([0-9a-f]+)">(.*?)</p>', source, re.S):
        text = html.unescape(re.sub(r"<[^>]*>", "", raw))
        paragraphs.append((text, paragraph_id))
    seen = set()
    stats = {"paragraphs": 0, "duplicate_occurrences": 0,
             "duplicate_non_md5_ids": 0, "first_occurrence_non_md5_ids": 0}
    exceptions = []
    for i, (text, paragraph_id) in enumerate(paragraphs):
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        duplicate = text in seen
        stats["paragraphs"] += 1
        if duplicate:
            stats["duplicate_occurrences"] += 1
            if paragraph_id != digest:
                stats["duplicate_non_md5_ids"] += 1
                exceptions.append({"index": i, "text": text, "id": paragraph_id})
        elif paragraph_id != digest:
            stats["first_occurrence_non_md5_ids"] += 1
        seen.add(text)
    result[str(part_id)] = {**stats, "exceptions_sample": exceptions[:3]}
print(json.dumps(result, indent=2, ensure_ascii=False))
(here / "wattpad-id-control.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
