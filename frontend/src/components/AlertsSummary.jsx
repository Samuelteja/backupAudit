// frontend/src/components/AlertsSummary.jsx
import React, { useState, useEffect } from 'react';
import { getAlertsSummary } from '../services/api';

// A small, reusable component for each individual KPI card
const SummaryCard = ({ title, value, bgColor, textColor }) => {
  return (
    <div className={`p-4 rounded-lg shadow-md ${bgColor} ${textColor}`}>
      <h3 className="text-sm font-semibold uppercase">{title}</h3>
      <p className="text-3xl font-bold mt-2">
        {value !== null ? value : 'N/A'}
      </p>
    </div>
  );
};

function AlertsSummary() {
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setIsLoading(true);
        const response = await getAlertsSummary();
        setSummary(response.data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch alerts summary:", err);
        setError("Could not load summary data.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, []); // Empty array ensures this runs only once on mount

  if (isLoading) {
    return <div className="text-center p-4">Loading summary...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">{error}</div>;
  }

  // Fallback in case the API returns no data for some reason
  if (!summary) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <SummaryCard 
        title="New (Unread) Alerts" 
        value={summary.new_unread_count}
        bgColor="bg-blue-500"
        textColor="text-white"
      />
      <SummaryCard 
        title="Critical Alerts (24h)" 
        value={summary.critical_count_24h}
        bgColor="bg-red-600"
        textColor="text-white"
      />
      <SummaryCard 
        title="Warning Alerts (24h)" 
        value={summary.warning_count_24h}
        bgColor="bg-yellow-400"
        textColor="text-gray-800"
      />
      <SummaryCard 
        title="Backup Success Rate (24h)" 
        value={summary.backup_success_rate_24h !== null ? `${summary.backup_success_rate_24h.toFixed(1)}%` : 'N/A'}
        bgColor="bg-green-500"
        textColor="text-white"
      />
    </div>
  );
}

export default AlertsSummary;