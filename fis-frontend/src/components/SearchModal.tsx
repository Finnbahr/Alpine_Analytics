import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { globalSearch } from '../services/api';
import type { SearchResult } from '../types';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const searchDebounced = setTimeout(async () => {
      if (query.length >= 2) {
        setLoading(true);
        try {
          const data = await globalSearch(query, { limit: 10 });
          setResults(data);
        } catch (error) {
          console.error('Search failed:', error);
        } finally {
          setLoading(false);
        }
      } else {
        setResults(null);
      }
    }, 300);

    return () => clearTimeout(searchDebounced);
  }, [query]);

  const handleAthleteClick = (fisCode: string) => {
    navigate(`/athletes/${fisCode}`);
    onClose();
    setQuery('');
  };

  const handleLocationClick = (location: string) => {
    navigate(`/courses?location=${encodeURIComponent(location)}`);
    onClose();
    setQuery('');
  };

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto p-4 sm:p-6 md:p-20">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <Dialog.Panel className="mx-auto max-w-2xl transform divide-y divide-gray-100 overflow-hidden rounded-xl bg-white shadow-2xl ring-1 ring-black ring-opacity-5 transition-all">
              {/* Search Input */}
              <div className="relative">
                <MagnifyingGlassIcon className="pointer-events-none absolute left-4 top-3.5 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  className="h-12 w-full border-0 bg-transparent pl-11 pr-4 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm"
                  placeholder="Search athletes or locations..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  autoFocus
                />
                <button
                  onClick={onClose}
                  className="absolute right-4 top-3.5 text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              {/* Results */}
              {results && (
                <div className="max-h-96 overflow-y-auto p-2">
                  {/* Athletes */}
                  {results.results.athletes.length > 0 && (
                    <div className="mb-4">
                      <h3 className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
                        Athletes
                      </h3>
                      {results.results.athletes.map((athlete) => (
                        <button
                          key={athlete.fis_code}
                          onClick={() => handleAthleteClick(athlete.fis_code)}
                          className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md transition-colors"
                        >
                          <div className="font-medium text-gray-900">{athlete.name}</div>
                          <div className="text-sm text-gray-500">
                            {athlete.country && `${athlete.country} • `}
                            {athlete.wins !== null && `${athlete.wins} wins`}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Locations */}
                  {results.results.locations.length > 0 && (
                    <div>
                      <h3 className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
                        Locations
                      </h3>
                      {results.results.locations.map((loc, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleLocationClick(loc.location)}
                          className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md transition-colors"
                        >
                          <div className="font-medium text-gray-900">{loc.location}</div>
                          <div className="text-sm text-gray-500">
                            {loc.country && `${loc.country} • `}
                            {loc.race_count} races
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* No results */}
                  {results.total_results === 0 && (
                    <div className="px-6 py-14 text-center text-sm text-gray-500">
                      No results found for "{query}"
                    </div>
                  )}
                </div>
              )}

              {/* Loading */}
              {loading && (
                <div className="px-6 py-14 text-center text-sm text-gray-500">
                  Searching...
                </div>
              )}

              {/* Initial state */}
              {!query && !results && (
                <div className="px-6 py-14 text-center text-sm text-gray-500">
                  Start typing to search for athletes or locations
                </div>
              )}
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
}
