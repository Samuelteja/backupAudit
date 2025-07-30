// src/components/MainLayout.jsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

function MainLayout() {
  return (
    <div className="flex h-screen bg-gray-100">
      
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-y-auto">
        <Header />
        <main className="flex-grow p-6">
          <Outlet />
        </main>

      </div>
    </div>
  );
}

export default MainLayout;