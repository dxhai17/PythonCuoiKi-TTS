"""Rule-based text parser, abbreviation filter, and 35-word clause sub-segmentation engine."""

from __future__ import annotations

import re
from typing import Any

# Common English and Latin abbreviations to protect from premature sentence splitting
ABBREVIATIONS = {
    "Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Jr", "Gen", "Col", "Capt", "Lt",
    "e.g", "i.e", "vs", "etc", "approx", "dept", "est", "govt", "inc", "ltd", "corp",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec",
    "St", "Ave", "Rd", "Blvd"
}

_ABBR_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(abbr) for abbr in ABBREVIATIONS) + r")\.",
    re.IGNORECASE
)
_ABBR_PLACEHOLDER = "___DOT___"


def _protect_abbreviations(text: str) -> str:
    """Replace period in common abbreviations with placeholder."""
    return _ABBR_PATTERN.sub(r"\1" + _ABBR_PLACEHOLDER, text)


def _restore_abbreviations(text: str) -> str:
    """Restore period in common abbreviations."""
    return text.replace(_ABBR_PLACEHOLDER, ".")


def _split_long_clause(sentence: str, max_words: int = 35) -> list[str]:
    """
    Sub-segment long sentences exceeding max_words on clause boundaries
    (; , : — --) to preserve natural speaking cadence and avoid TTS timeouts.
    """
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence]

    # Split on clause punctuation while keeping delimiters
    clause_delims = re.compile(r"([;:\—\–]|--|,)\s*")
    parts = clause_delims.split(sentence)

    # Reconstruct clauses with their trailing delimiter
    chunks: list[str] = []
    current_clause = ""
    i = 0
    while i < len(parts):
        chunk = parts[i]
        delim = parts[i + 1] if (i + 1) < len(parts) else ""
        combined = (chunk + delim).strip()
        i += 2

        if not combined:
            continue

        if not current_clause:
            current_clause = combined
        elif len((current_clause + " " + combined).split()) <= max_words:
            current_clause = f"{current_clause} {combined}"
        else:
            chunks.append(current_clause.strip())
            current_clause = combined

    if current_clause.strip():
        chunks.append(current_clause.strip())

    # Fallback if sentence had no punctuation delimiters: hard space chunking
    if len(chunks) == 1 and len(chunks[0].split()) > max_words:
        raw_words = chunks[0].split()
        chunks = []
        for k in range(0, len(raw_words), max_words):
            chunks.append(" ".join(raw_words[k:k + max_words]))

    return chunks


def tokenize_sentences(text: str, max_clause_words: int = 35) -> list[str]:
    """
    Tokenize raw text into clean, ordered sentences adhering to the 35-word clause rule.
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace and newlines
    cleaned = re.sub(r"\r\n|\r", "\n", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # Protect abbreviations
    protected = _protect_abbreviations(cleaned)

    # Split on standard sentence-ending punctuation followed by whitespace or newline
    sentence_candidates = re.split(r"(?<=[.!?])\s+", protected)

    results: list[str] = []
    for cand in sentence_candidates:
        cand_str = _restore_abbreviations(cand).strip()
        if not cand_str:
            continue

        # Sub-segment sentences that exceed max_clause_words
        sub_sentences = _split_long_clause(cand_str, max_words=max_clause_words)
        for s in sub_sentences:
            cleaned_s = s.strip()
            if cleaned_s:
                results.append(cleaned_s)

    return results


def split_into_chapters_and_sentences(
    document_text: str, max_clause_words: int = 35
) -> list[dict[str, Any]]:
    """
    Detect chapters (Markdown headings or 'Chapter N') and partition into structured sections.
    """
    lines = document_text.splitlines()
    chapters: list[dict[str, Any]] = []

    current_title = "Chapter 1"
    current_lines: list[str] = []
    chapter_heading_re = re.compile(
        r"^(?:#{1,3}\s+(.+)|(?:chapter|section|part)\s+[\dIVXLCDM]+.*)",
        re.IGNORECASE
    )

    for line in lines:
        stripped = line.strip()
        match = chapter_heading_re.match(stripped)
        if match:
            # If we already accumulated content, finalize previous chapter
            if current_lines:
                body = "\n".join(current_lines).strip()
                sentences = tokenize_sentences(body, max_clause_words=max_clause_words)
                if sentences:
                    chapters.append({
                        "title": current_title,
                        "sentences": sentences,
                    })
                current_lines = []

            # Extract title
            if stripped.startswith("#"):
                current_title = re.sub(r"^#+\s*", "", stripped).strip()
            else:
                current_title = stripped
        else:
            current_lines.append(line)

    # Process remaining content
    if current_lines:
        body = "\n".join(current_lines).strip()
        sentences = tokenize_sentences(body, max_clause_words=max_clause_words)
        if sentences:
            chapters.append({
                "title": current_title,
                "sentences": sentences,
            })

    # If document had no chapter headings, wrap in a single Chapter 1
    if not chapters:
        sentences = tokenize_sentences(document_text, max_clause_words=max_clause_words)
        if sentences:
            chapters.append({
                "title": "Chapter 1",
                "sentences": sentences,
            })

    return chapters
