// src/App.jsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';

// Import Providers and Route Guards
import { AuthProvider } from './context/AuthProvider';
import ProtectedRoute from './components/ProtectedRoute';

// Import Layouts
import MainLayout from './components/MainLayout';

// Import Pages
import SignUpPage from './pages/SignUpPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './components/DashboardPage';
import TeamManagementPage from './pages/TeamManagementPage'; 
import RiskDiscoveryPage from './pages/RiskDiscoveryPage'; 
import AlertsDashboardPage from './pages/AlertsDashboardPage';
import JobDetailsPage from './pages/JobDetailsPage';

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* === PUBLIC ROUTES === */}
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* === PROTECTED ROUTES === */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/team" element={<TeamManagementPage />} />
            <Route path="/risk" element={<RiskDiscoveryPage />} />
            <Route path="/alerts" element={<AlertsDashboardPage />} />
            <Route path="/jobs/details/:jobId" element={<JobDetailsPage />} />
          </Route>
        </Route>
        
      </Routes>
    </AuthProvider>
  );
}

export default App;