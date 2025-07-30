// src/pages/SignUpPage.jsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { signup } from '../services/api';
import Button from '../components/ui/Button'; // Assuming you have a Button component

function SignUpPage() {
  const [tenantName, setTenantName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // No change to the logic!
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await signup(tenantName, email, password);
      navigate('/login');
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    }
  };

  return (
    // Main container: full screen height, gray background, centers content
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      {/* Form card: white background, padding, rounded corners, shadow, max width */}
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
        
        {/* Header */}
        <h2 className="text-2xl font-bold text-center text-gray-900">
          Create Your Account
        </h2>

        {/* Form */}
        <form className="space-y-6" onSubmit={handleSubmit}>
          {/* Company Name Field */}
          <div>
            <label htmlFor="tenantName" className="block text-sm font-medium text-gray-700">
              Company Name
            </label>
            <input
              id="tenantName"
              type="text"
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
              required
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Email Field */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Your Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Error Message Display */}
          {error && <p className="text-sm text-center text-red-500">{error}</p>}

          {/* Submit Button */}
          <div>
            <Button type="submit">Sign Up</Button>
          </div>
        </form>
        
        {/* Link to Login */}
        <p className="text-sm text-center text-gray-600">
          Already have an account?{' '}
          <a href="/login" className="font-medium text-blue-600 hover:underline">
            Log In
          </a>
        </p>
      </div>
    </div>
  );
}

export default SignUpPage;