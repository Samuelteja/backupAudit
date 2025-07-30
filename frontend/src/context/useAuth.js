// src/context/useAuth.js
import { useContext } from 'react';
import { AuthContext } from './AuthContext'; // <-- It imports from the new, tiny file

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};