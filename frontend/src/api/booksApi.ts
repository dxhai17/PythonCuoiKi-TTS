import { apiGet, apiUpload } from './client.ts';
import { Book, BookUploadResponse } from '../types/book.ts';

export async function listBooks(limit = 50, offset = 0): Promise<Book[]> {
  return apiGet<Book[]>('/books', { limit, offset });
}

export async function getBookDetail(bookId: number): Promise<Book> {
  return apiGet<Book>(`/books/${bookId}`);
}

export async function uploadBookFile(
  file: File,
  title?: string,
  author?: string
): Promise<BookUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);
  if (author) formData.append('author', author);

  return apiUpload<BookUploadResponse>('/books/ingest', formData);
}
