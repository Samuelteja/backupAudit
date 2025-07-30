// src/components/Sidebar.jsx
import React from 'react';
import { Link, NavLink } from 'react-router-dom'; // Using NavLink is even better for styling active links

function Sidebar() {
  // This function is used by NavLink to apply a different style when the link is active
  /*
  const getLinkClass = ({ isActive }) =>
    isActive
      ? 'bg-gray-700 text-white' // Style for the active link
      : 'text-gray-300 hover:bg-gray-700 hover:text-white'; // Style for inactive links

  */

  return (
    // Main container: dark background, fixed width, padding, flexbox column layout
    <div className="flex flex-col w-32 bg-gray-800 text-white">
      
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
          {/* We will conditionally render the 'Team Management' link here in a later step */}
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