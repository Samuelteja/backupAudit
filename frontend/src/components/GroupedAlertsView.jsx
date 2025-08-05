// frontend/src/components/GroupedAlertsView.jsx
import React, { useState, useEffect } from 'react';
import { getGroupedAlerts } from '../services/api'; // The API function we'll create

/**
 * A single, reusable card component to display one group of alerts.
 * It receives a single 'alertGroup' object as a prop.
 */
const GroupedAlertCard = ({ alertGroup, onDrillDown }) => {
  
  // Helper function to determine the color of the left border
  const getSeverityClass = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'major':
        return 'border-l-4 border-red-500';
      case 'warning':
      case 'minor':
        return 'border-l-4 border-yellow-500';
      default:
        return 'border-l-4 border-gray-400';
    }
  };

  return (
    // --- THIS IS THE CORRECTED SINGLE ROOT DIV ---
    // It combines the onClick handler, the cursor-pointer style,
    // and all the other styling properties into one element.
    <div 
      onClick={() => onDrillDown(alertGroup.alert_name)} 
      className={`bg-white p-4 rounded-lg shadow-md transition-shadow hover:shadow-lg cursor-pointer ${getSeverityClass(alertGroup.severity)}`}
    >
      {/* --- Card Header --- */}
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-gray-800 text-lg">{alertGroup.alert_name}</h3>
          <p className="text-sm text-gray-500">Severity: {alertGroup.severity}</p>
        </div>
        <div className="text-right flex-shrink-0 ml-4">
          <p className="text-3xl font-bold text-gray-800">{alertGroup.occurrence_count}</p>
          <p className="text-xs text-gray-500">Occurrences</p>
        </div>
      </div>

      {/* --- Card Body --- */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-600 mb-2">Top Affected Clients</h4>
        {alertGroup.top_affected_clients.length > 0 ? (
          <ul className="text-sm text-gray-700 space-y-1">
            {alertGroup.top_affected_clients.map(client => (
              <li key={client.client_name} className="flex justify-between items-center">
                <span className="truncate pr-2">{client.client_name}</span>
                <span className="font-semibold bg-gray-200 text-gray-700 text-xs px-2 py-1 rounded-full">{client.count} times</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-500 italic">No specific client data available.</p>
        )}
      </div>

      {/* --- Card Footer --- */}
      <div className="mt-3 text-right text-xs text-gray-400">
        Last seen: {new Date(alertGroup.last_seen).toLocaleString()}
      </div>
    </div>
  );
};


/**
 * The main view component that fetches and displays all the grouped alert cards.
 */
function GroupedAlertsView({ onDrillDown }) {
  const [groupedAlerts, setGroupedAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const severityOrder = {
      "critical": 1,
      "major": 2,
      "minor": 3,
      "warning": 4,
      "information": 5
    };
    const fetchGroupedAlerts = async () => {
      try {
        setIsLoading(true);
        const response = await getGroupedAlerts();
        const sortedData = response.data.sort((a, b) => {
          // Get the numeric severity level, defaulting to a high number if not found
          const severityA = severityOrder[a.severity.toLowerCase()] || 99;
          const severityB = severityOrder[b.severity.toLowerCase()] || 99;

          // First, compare by severity level
          if (severityA !== severityB) {
            return severityA - severityB; // Lower number (Critical) comes first
          }

          // If severities are the same, compare by occurrence count (descending)
          return b.occurrence_count - a.occurrence_count;
        });
        
        setGroupedAlerts(sortedData);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch grouped alerts:", err);
        setError("Could not load summary data. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchGroupedAlerts();
  }, []); // The empty array ensures this effect runs only once when the component mounts

  // --- Render Logic ---

  if (isLoading) {
    return <div className="text-center p-8 text-gray-500">Analyzing alert patterns...</div>;
  }

  if (error) {
    return <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">{error}</div>;
  }
  
  if (groupedAlerts.length === 0) {
    return (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded" role="alert">
            <strong className="font-bold">No Alert Patterns Found. </strong>
            <span className="block sm:inline">The system is quiet.</span>
        </div>
    );
  }

  return (
    // This grid layout will automatically wrap the cards on different screen sizes.
    <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-6">
      {groupedAlerts.map((group) => (
        // We create a unique key for React to track each card efficiently
        <GroupedAlertCard key={`${group.alert_name}-${group.severity}`} alertGroup={group} onDrillDown={onDrillDown} />
      ))}
    </div>
  );
}

export default GroupedAlertsView;