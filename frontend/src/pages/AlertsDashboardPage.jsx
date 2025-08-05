// frontend/src/pages/AlertsDashboardPage.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { getAlerts, markAlertAsRead } from '../services/api';
import GroupedAlertsView from '../components/GroupedAlertsView';
import { useDebounce } from '../hooks/useDebounce';
// A reusable component for the alert table
const AlertsTable = ({ alerts, filters, setFilters, onAcknowledge }) => {
  const [acknowledgingId, setAcknowledgingId] = useState(null);
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prevFilters => ({
      ...prevFilters,
      [name]: value,
    }));
  };
  const getSeverityClass = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'major': return 'bg-red-100 text-red-800';
      case 'minor': return 'bg-yellow-100 text-yellow-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleAcknowledge = async (alertId) => {
    setAcknowledgingId(alertId);
    try {
      await markAlertAsRead(alertId);
      onAcknowledge();
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
      setAcknowledgingId(null);
    }
  };

  const handleClearFilters = () => {
    setFilters({ alertName: '', severity: '' });
  };

  const isFilterActive = filters.alertName || filters.severity;

  return (
    <table className="min-w-full bg-white">
      <thead className="bg-gray-50">
        <tr>
          <th className="w-1/6 py-3 px-4 uppercase font-semibold text-sm text-left">
            <select
              name="severity"
              value={filters.severity || ''}
              onChange={handleFilterChange}
              className="w-full bg-gray-50 border-gray-300 rounded-md shadow-sm"
            >
              <option value="">Severity</option>
              <option value="Critical">Critical</option>
              <option value="Major">Major</option>
              <option value="Warning">Warning</option>
              <option value="Minor">Minor</option>
            </select>
          </th>
          <th className="w-1/4 py-3 px-4 uppercase font-semibold text-sm text-left">
            <input
              type="text"
              name="alertName"
              value={filters.alertName || ''}
              onChange={handleFilterChange}
              placeholder="Filter by Alert Type..."
              className="w-full px-2 py-1 border border-gray-300 rounded-md"
            />
          </th>
          <th className="w-1/2 py-3 px-4 uppercase font-semibold text-sm text-left">Details</th>
          <th className="w-1/4 py-3 px-4 uppercase font-semibold text-sm text-left">Detected Time</th>
          <th className="w-1/6 py-3 px-4 uppercase font-semibold text-sm text-left">
            {/* We conditionally render the button ONLY if a filter is active */}
            {isFilterActive && (
              <button 
                onClick={handleClearFilters}
                className="text-blue-500 hover:text-blue-700 text-xs font-bold"
              >
                Clear Filters
              </button>
            )}
          </th>
        </tr>
      </thead>
      <tbody className="text-gray-700">
        {alerts.length > 0 ? (
          alerts.map((alert) => (
            <tr key={alert.id} className="border-b border-gray-200 hover:bg-gray-50">
            <td className={`py-3 px-4 ${getSeverityClass(alert.severity)}`}>{alert.severity}</td>
            <td className="py-3 px-4">{alert.alert_name}</td>
            <td className="py-3 px-4">{alert.details}</td>
            <td className="py-3 px-4">{new Date(alert.event_timestamp).toLocaleString()}</td>
            <td className="py-3 px-4">
              {/* If the alert is unread, show the button */}
              {!alert.is_read && (
                <button
                  onClick={() => handleAcknowledge(alert.id)}
                  disabled={acknowledgingId === alert.id}
                  className={`font-bold py-1 px-3 rounded text-xs text-white ${
                    acknowledgingId === alert.id
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-500 hover:bg-blue-700'
                  }`}
                >
                  {acknowledgingId === alert.id ? 'Thanks for acknowledging!' : 'Acknowledge'}
                </button>
              )}
            </td>
          </tr>
          ))
        ) : (
          <tr>
            <td colSpan="5" className="text-center py-8 text-gray-500">
              No alerts match your current filters.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
};

function AlertsDashboardPage() {
  const [viewMode, setViewMode] = useState('summary');
  const [filters, setFilters] = useState({ alertName: '', severity: '' });
  const debouncedFilters = useDebounce(filters, 500); // 500ms is a good delay

  // State to hold the "master list" of alerts from the API
  const [allUnreadAlerts, setAllUnreadAlerts] = useState([]);
  const [allReadAlerts, setAllReadAlerts] = useState([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAlerts = async (currentFilters) => {
    setIsLoading(true);
    try {
      const response = await getAlerts(currentFilters);
      // Store the full, unfiltered list when the component loads or filters are cleared
      if (!currentFilters.alertName && !currentFilters.severity) {
        setAllUnreadAlerts(response.data.unread_alerts);
        setAllReadAlerts(response.data.read_alerts);
      }
      // We will now filter this master list on the client side
      setError(null);
    } catch (err) {
      console.error("Failed to fetch alerts:", err);
      setError("Could not load alerts.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'list') {
      // Only re-fetch from API if the debounced filters change
      fetchAlerts(debouncedFilters);
    }
  }, [viewMode, debouncedFilters]);

  /*
  
  const clearFilter = () => {
    setAlertFilter(null);
  };
  */
  const ViewModeToggle = () => (
    <div className="flex justify-center mb-6">
      <div className="bg-gray-200 rounded-lg p-1 flex">
        <button 
          onClick={() => setViewMode('summary')}
          className={`px-4 py-2 text-sm font-semibold rounded-md ${viewMode === 'summary' ? 'bg-white shadow' : 'text-gray-600'}`}
        >
          Summary View
        </button>
        <button 
          onClick={() => setViewMode('list')}
          className={`px-4 py-2 text-sm font-semibold rounded-md ${viewMode === 'list' ? 'bg-white shadow' : 'text-gray-600'}`}
        >
          List View
        </button>
      </div>
    </div>
  );

  const filteredUnreadAlerts = useMemo(() => {
    return allUnreadAlerts.filter(alert => {
      const nameMatch = filters.alertName ? alert.alert_name.toLowerCase().includes(filters.alertName.toLowerCase()) : true;
      const severityMatch = filters.severity ? alert.severity === filters.severity : true;
      return nameMatch && severityMatch;
    });
  }, [allUnreadAlerts, filters]);

  const filteredReadAlerts = useMemo(() => {
    return allReadAlerts.filter(alert => {
      const nameMatch = filters.alertName ? alert.alert_name.toLowerCase().includes(filters.alertName.toLowerCase()) : true;
      const severityMatch = filters.severity ? alert.severity === filters.severity : true;
      return nameMatch && severityMatch;
    });
  }, [allReadAlerts, filters]);


  const handleDrillDown = (alertName) => {
    setFilters({ severity: '', alertName: alertName });
    setViewMode('list');
  };

  if (isLoading) {
    return <div className="text-center p-8">Loading Alerts...</div>;
  }

  if (error) {
    return <div className="bg-red-100 text-red-700 p-4 rounded">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Alerts Dashboard</h1>
      <ViewModeToggle setViewMode={setViewMode} viewMode={viewMode} />

      {viewMode === 'summary' ? (
        <GroupedAlertsView onDrillDown={handleDrillDown} />
      ) : (
        <>
          {isLoading ? (
            <div className="text-center p-8">Loading Alerts...</div>
          ) : error ? (
            <div className="bg-red-100 text-red-700 p-4 rounded">{error}</div>
          ) : (
            // --- THIS LOGIC IS NOW MUCH CLEANER ---
            <>
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h2 className="text-xl font-bold mb-4">New Alerts Requiring Attention</h2>
                {/* We just render the table and pass it the data. It handles the empty state itself. */}
                <AlertsTable 
                  alerts={filteredUnreadAlerts} 
                  filters={filters}
                  setFilters={setFilters}
                  onAcknowledge={() => fetchAlerts(debouncedFilters)}
                />
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h2 className="text-xl font-bold mb-4">Recent Alert History</h2>
                {/* Same for the history table */}
                <AlertsTable 
                  alerts={filteredReadAlerts} 
                  filters={filters}
                  setFilters={setFilters}
                  onAcknowledge={() => {}} 
                />
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default AlertsDashboardPage;