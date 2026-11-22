"""Pydantic validation schemas for Book catalog and ingestion."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BookSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    total_chapters: int
    total_sentences: int
    total_words: int
    created_at: str | None = None


class BookDetailResponse(BookSummaryResponse):
    source_path: str
    content_hash: str


class BookSentenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sentence_index: int
    chapter_index: int
    text_content: str
    word_count: int


class BookSentencesListResponse(BaseModel):
    book_id: int
    total_sentences: int
    sentences: list[BookSentenceResponse]


class BookUploadSuccessResponse(BaseModel):
    status: str = "success"
    book_id: int
    title: str
    total_chapters: int
    total_sentences: int
    total_words: int
