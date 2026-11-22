import { useState } from 'react';
import { Navbar } from './components/Navbar/Navbar.tsx';
import { LibraryPage } from './pages/LibraryPage.tsx';
import { PlayerPage } from './pages/PlayerPage.tsx';
import { DashboardPage } from './pages/DashboardPage.tsx';
import { Book } from './types/book.ts';

export function App() {
  const [currentTab, setCurrentTab] = useState<'library' | 'player' | 'dashboard'>('library');
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);

  const handleSelectBook = (book: Book) => {
    setSelectedBook(book);
    setCurrentTab('player');
  };

  return (
    <div className="app-layout">
      <Navbar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
      />

      <main className="main-container">
        {currentTab === 'library' && (
          <LibraryPage onSelectBook={handleSelectBook} />
        )}

        {currentTab === 'player' && selectedBook && (
          <PlayerPage
            bookId={selectedBook.id}
            bookTitle={selectedBook.title}
            onBackToLibrary={() => setCurrentTab('library')}
          />
        )}

        {currentTab === 'player' && !selectedBook && (
          <div className="empty-state">
            <h3>No Book Selected</h3>
            <p>Please select a book from the library to start listening.</p>
            <button className="btn-primary" onClick={() => setCurrentTab('library')}>
              Go to Library
            </button>
          </div>
        )}

        {currentTab === 'dashboard' && (
          <DashboardPage />
        )}
      </main>
    </div>
  );
}

export default App;
