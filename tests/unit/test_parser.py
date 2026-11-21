"""Unit tests for text ingestion parser and 35-word clause boundary segmentation."""

from __future__ import annotations

from src.ingestion.parser import split_into_chapters_and_sentences, tokenize_sentences


def test_standard_sentence_splitting():
    text = "The morning sun was shining bright. It was a peaceful day! Would you join us on the journey?"
    sentences = tokenize_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "The morning sun was shining bright."
    assert sentences[1] == "It was a peaceful day!"
    assert sentences[2] == "Would you join us on the journey?"


def test_abbreviation_preservation():
    text = "Dr. Watson visited Mr. Holmes at 221B Baker St. in London. They discussed e.g. recent criminal cases."
    sentences = tokenize_sentences(text)
    # Shouldn't split on Dr. or Mr. or St. or e.g.
    assert len(sentences) == 2
    assert "Dr. Watson" in sentences[0]
    assert "They discussed" in sentences[1]


def test_35_word_clause_boundary_subsegmentation():
    # Construct a sentence with > 35 words separated by semicolons and commas
    clause1 = "In the heart of the ancient forest where towering emerald pines whispered timeless secrets to the rushing river below"
    clause2 = "an unexpected traveler paused to catch his breathless reflection in the crystalline water"
    clause3 = "wondering whether the legendary sanctuary lay just beyond the foggy mountain ridge"
    full_sentence = f"{clause1}; {clause2}, {clause3}."

    total_words = len(full_sentence.split())
    assert total_words > 35

    segments = tokenize_sentences(full_sentence, max_clause_words=35)
    # The parser must have split the run-on sentence at clause boundaries
    assert len(segments) > 1
    for seg in segments:
        assert len(seg.split()) <= 35 or not any(p in seg for p in (";", ":", "—", "--", ","))


def test_chapter_and_sentence_extraction():
    doc = """
# Chapter 1: The First Steps

It was dark when they departed. The trail was steep and narrow.

## Chapter 2: The High Pass

Snow began falling gently. The wind picked up quickly.
    """
    chapters = split_into_chapters_and_sentences(doc)
    assert len(chapters) == 2
    assert chapters[0]["title"] == "Chapter 1: The First Steps"
    assert len(chapters[0]["sentences"]) == 2
    assert chapters[1]["title"] == "Chapter 2: The High Pass"
    assert len(chapters[1]["sentences"]) == 2
