import React from 'react';
import { Book as BookType } from '../../types/book.ts';
import { Headphones, BookOpen, Layers } from 'lucide-react';

interface BookCardProps {
  book: BookType;
  onSelect: (book: BookType) => void;
}

export const BookCard: React.FC<BookCardProps> = ({ book, onSelect }) => {
  return (
    <div className="book-card">
      <div className="book-card-header">
        <h3 className="book-card-title">{book.title}</h3>
        <span className="book-card-author">by {book.author}</span>
      </div>

      <div className="book-card-stats">
        <div className="stat-pill">
          <Layers size={14} />
          <span>{book.total_chapters} {book.total_chapters === 1 ? 'Chapter' : 'Chapters'}</span>
        </div>
        <div className="stat-pill">
          <BookOpen size={14} />
          <span>{book.total_sentences} Sentences</span>
        </div>
        <div className="stat-pill">
          <span>{book.total_words.toLocaleString()} Words</span>
        </div>
      </div>

      <div className="book-card-footer">
        <button className="listen-btn" onClick={() => onSelect(book)}>
          <Headphones size={16} />
          <span>Listen</span>
        </button>
      </div>
    </div>
  );
};
