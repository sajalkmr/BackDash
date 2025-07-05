import React from 'react';
import { Link } from 'react-router-dom';

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  return (
    <header className="bg-white shadow">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          <nav>
            <ul className="flex space-x-6">
              <li>
                <Link to="/" className="text-gray-600 hover:text-gray-900">
                  Strategy Builder
                </Link>
              </li>
              <li>
                <Link to="/analytics" className="text-gray-600 hover:text-gray-900">
                  Analytics
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
}