import React from 'react';
import { BookOpen, Headphones, BarChart2 } from 'lucide-react';

interface NavbarProps {
  currentTab: 'library' | 'player' | 'dashboard';
  onSelectTab: (tab: 'library' | 'player' | 'dashboard') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab }) => {
  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand" onClick={() => onSelectTab('library')}>
          <BookOpen className="brand-icon" size={24} />
          <span className="brand-name">StudyLab</span>
          <span className="brand-tag">Audiobook</span>
        </div>

        <nav className="navbar-links">
          <button
            className={`nav-btn ${currentTab === 'library' ? 'active' : ''}`}
            onClick={() => onSelectTab('library')}
          >
            <BookOpen size={18} />
            <span>Library</span>
          </button>

          <button
            className={`nav-btn ${currentTab === 'player' ? 'active' : ''}`}
            onClick={() => onSelectTab('player')}
          >
            <Headphones size={18} />
            <span>Player</span>
          </button>

          <button
            className={`nav-btn ${currentTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => onSelectTab('dashboard')}
          >
            <BarChart2 size={18} />
            <span>Dashboard</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
