import { Link } from 'react-router-dom';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import SearchModal from './SearchModal';

export default function Header() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  return (
    <>
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-3">
              <div className="text-2xl font-bold text-primary-600">⛷️</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">FIS Alpine Analytics</h1>
                <p className="text-xs text-gray-500">Professional Ski Racing Data</p>
              </div>
            </Link>

            {/* Search */}
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-500" />
              <span className="text-gray-600">Search athletes...</span>
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-primary-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 h-12 items-center">
            <NavLink to="/">Home</NavLink>
            <NavLink to="/leaderboards">Leaderboards</NavLink>
            <NavLink to="/athletes">Athletes</NavLink>
            <NavLink to="/races">Races</NavLink>
            <NavLink to="/courses">Courses</NavLink>
            <NavLink to="/analytics">Analytics</NavLink>
          </div>
        </div>
      </nav>

      <SearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </>
  );
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="text-white hover:text-primary-100 transition-colors font-medium text-sm"
    >
      {children}
    </Link>
  );
}
