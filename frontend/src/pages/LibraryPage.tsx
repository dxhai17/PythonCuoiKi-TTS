import React, { useState } from 'react';
import { Book } from '../types/book.ts';
import { useBookCatalog } from '../hooks/useBookCatalog.ts';
import { BookCard } from '../components/Library/BookCard.tsx';
import { BookUploaderModal } from '../components/BookUploader/BookUploaderModal.tsx';
import { Plus, Search, BookOpen } from 'lucide-react';

interface LibraryPageProps {
  onSelectBook: (book: Book) => void;
}

export const LibraryPage: React.FC<LibraryPageProps> = ({ onSelectBook }) => {
  const { books, isLoading, error, uploadBook } = useBookCatalog();
  const [search, setSearch] = useState('');
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const filteredBooks = books.filter((b) =>
    b.title.toLowerCase().includes(search.toLowerCase()) ||
    b.author.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="library-page">
      <div className="library-toolbar">
        <div className="search-box">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search audiobooks"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <button className="btn-primary" onClick={() => setIsUploadOpen(true)}>
          <Plus size={18} />
          <span>Upload Book</span>
        </button>
      </div>

      {isLoading && books.length === 0 ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading library catalog...</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
        </div>
      ) : filteredBooks.length === 0 ? (
        <div className="empty-state">
          <BookOpen size={48} className="empty-icon" />
          <h3>No Audiobooks Found</h3>
          <p>Get started by uploading a .txt or .md book file to your library.</p>
          <button className="btn-primary" onClick={() => setIsUploadOpen(true)}>
            <Plus size={18} />
            <span>Upload Your First Book</span>
          </button>
        </div>
      ) : (
        <div className="books-grid">
          {filteredBooks.map((b) => (
            <BookCard key={b.id} book={b} onSelect={onSelectBook} />
          ))}
        </div>
      )}

      <BookUploaderModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={uploadBook}
      />
    </div>
  );
};
