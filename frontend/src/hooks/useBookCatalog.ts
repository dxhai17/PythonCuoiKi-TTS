import { useState, useEffect, useCallback } from 'react';
import { Book } from '../types/book.ts';
import { listBooks, uploadBookFile } from '../api/booksApi.ts';

export function useBookCatalog() {
  const [books, setBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshBooks = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await listBooks();
      setBooks(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load library books');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshBooks();
  }, [refreshBooks]);

  const uploadBook = useCallback(async (file: File, title?: string, author?: string) => {
    const res = await uploadBookFile(file, title, author);
    await refreshBooks();
    return res;
  }, [refreshBooks]);

  return {
    books,
    isLoading,
    error,
    uploadBook,
    refreshBooks,
  };
}
