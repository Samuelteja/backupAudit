// src/pages/RiskDiscoveryPage.jsx
import React, { useState, useEffect } from 'react';
import { getUnprotectedAssets } from '../services/api';

function RiskDiscoveryPage() {
  const [unprotectedAssets, setUnprotectedAssets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        setIsLoading(true);
        console.log("Fetching unprotected assets...");
        const response = await getUnprotectedAssets();
        setUnprotectedAssets(response.data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch unprotected assets:", err);
        setError("Could not load asset data. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchAssets();
  }, []); // The empty dependency array means this runs once when the component mounts

  // --- Render Logic ---

  if (isLoading) {
    return <div className="text-center p-8">Loading asset inventory...</div>;
  }

  if (error) {
    return <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">{error}</div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">Unprotected Asset Discovery</h1>
      
      {unprotectedAssets.length === 0 ? (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative">
          <strong className="font-bold">All Clear! </strong>
          <span className="block sm:inline">No unprotected assets were found. All discovered VMs are protected.</span>
        </div>
      ) : (
        <div>
          <p className="mb-4 text-gray-600">The following virtual machines were discovered in your vCenter inventory but are not currently protected by a Commvault backup policy.</p>
          <table className="min-w-full bg-white">
            <thead className="bg-gray-800 text-white">
              <tr>
                <th className="text-left py-3 px-4 uppercase font-semibold text-sm">Unprotected Virtual Machine Name</th>
              </tr>
            </thead>
            <tbody className="text-gray-700">
              {unprotectedAssets.map((vmName, index) => (
                <tr key={index} className="border-b border-gray-200 hover:bg-gray-100">
                  <td className="text-left py-3 px-4">{vmName}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default RiskDiscoveryPage;