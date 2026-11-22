"""Pydantic validation schemas for Player, Bookmark, and Session entities."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: int
    current_chapter: int
    current_sentence_index: int
    completion_percentage: float
    last_read_at: str | None = None


class BookmarkUpdateRequest(BaseModel):
    book_id: int
    current_chapter: int = Field(default=1, ge=0)
    current_sentence_index: int = Field(ge=0)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class ReadingSessionCreateRequest(BaseModel):
    book_id: int
    duration_seconds: float = Field(ge=0)
    sentences_read: int = Field(default=0, ge=0)
    words_read: int = Field(default=0, ge=0)
    start_time: str
    end_time: str


class ReadingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    duration_seconds: int
    sentences_read: int
    words_read: int
    created_at: str | None = None
