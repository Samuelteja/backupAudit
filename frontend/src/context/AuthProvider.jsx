// src/context/AuthProvider.jsx
import React, { useState, useEffect} from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from './AuthContext'; // <-- IMPORT the context
import apiClient, { login as apiLogin, getUsersMe } from '../services/api';

// This file's only job is to export the Provider component.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('authToken') || null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const response = await getUsersMe();
          setUser(response.data);
        } catch (error) {
          console.error("Session verification failed", error);
          logout();
        }
      }
      setIsLoading(false);
    };
    verifyToken();
  }, [token]);

  const login = async (email, password) => {
    const response = await apiLogin(email, password);
    const newToken = response.data.access_token;
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
    navigate('/');
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('authToken');
    delete apiClient.defaults.headers.common['Authorization'];
    navigate('/login');
  };

  const value = { user, token, isLoading, login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}