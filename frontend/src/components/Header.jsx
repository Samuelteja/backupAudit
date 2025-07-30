// src/components/Header.jsx
import React from 'react';
import { useAuth } from '../context/useAuth';

function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6">
      <div className="tenant-info">
        <span className="text-gray-600">
          <span className="font-semibold">Tenant:</span> {user?.tenant?.name || '...'}
        </span>
      </div>
      <div className="user-info flex items-center">
        <span className="text-gray-800 mr-4">{user?.email || 'Loading...'}</span>
        {user && (
          <button 
            onClick={logout}
            className="bg-gray-800 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
}

export default Header;