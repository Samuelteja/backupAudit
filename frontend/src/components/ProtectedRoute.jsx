// src/components/ProtectedRoute.jsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/useAuth'; // Ensure this path is correct

function ProtectedRoute() {
  const { token, isLoading } = useAuth();

  // 1. While the AuthContext is verifying the token, we display a loading message.
  //    This prevents the dashboard from flashing on the screen momentarily.
  if (isLoading) {
    return <div>Loading session...</div>;
  }

  // 2. After loading is complete, we check for the token.
  //    If there is NO token, we redirect the user to the login page.
  //    The 'replace' prop is important for a good user experience.
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // 3. If loading is complete AND there is a token, we render the
  //    child components (i.e., the MainLayout and the Dashboard).
  return <Outlet />;
}

export default ProtectedRoute;