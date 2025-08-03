// src/components/Sidebar.jsx
import React from 'react';
import { Link, NavLink } from 'react-router-dom'; // Using NavLink is even better for styling active links
import { useAuth } from '../context/useAuth';
function Sidebar() {
  const { user } = useAuth();

  return (
    // Main container: dark background, fixed width, padding, flexbox column layout
    <div className="flex flex-col w-48 bg-gray-800 text-white">
      
      {/* App Logo/Title */}
      <div className="flex items-center justify-center h-16 border-b border-gray-700">
        <h1 className="text-2xl font-bold">Hokage</h1>
      </div>

      {/* Navigation Links */}
      <nav className="flex-grow p-4">
        <ul className="space-y-2">
          <li>
            {/* NavLink is like Link, but it knows when it's the "active" page */}
            <NavLink to="/" className={({ isActive }) => 
              `flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`
            }>
              {/* You can add icons here later */}
              <span>Dashboard</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/risk" className={({ isActive }) => 
              `flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`
            }>
              <span>Risk Discovery</span>
            </NavLink>
          </li>
          {user && (user.role === 'owner' || user.role === 'admin') && (
            <li>
              <NavLink to="/team" className={({ isActive }) => 
              `flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`
            }>
                <span>Team Management</span>
              </NavLink>
            </li>
          )}
          
        </ul>
      </nav>

      {/* (Optional) Footer or Profile section at the bottom */}
      <div className="p-4 border-t border-gray-700">
        {/* Profile info can go here */}
      </div>
    </div>
  );
}

export default Sidebar;