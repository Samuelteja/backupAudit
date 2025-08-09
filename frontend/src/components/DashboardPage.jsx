// src/pages/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/useAuth';
import { getJobs } from '../services/api';
import AlertsSummary from './AlertsSummary';
import { Link } from 'react-router-dom';

function DashboardPage() {
  const { user } = useAuth();
  
  // State for holding the list of jobs from the API
  const [jobs, setJobs] = useState([]);
  // State to track if we are currently fetching data
  const [isLoading, setIsLoading] = useState(true);
  // State to hold any potential error messages
  const [error, setError] = useState(null);

  // useEffect hook to fetch data when the component first loads
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setError(null); // Clear previous errors
        setIsLoading(true); // We are starting to load
        const response = await getJobs();
        setJobs(response.data); // Store the fetched jobs in state
      } catch (err) {
        setError("Failed to fetch backup jobs. Please try again later.");
        console.error(err);
      } finally {
        // This runs whether the fetch succeeded or failed
        setIsLoading(false); // We are done loading
      }
    };

    fetchJobs();
  }, []); // The empty array [] ensures this effect runs only ONCE

  const renderTableContent = () => {
    if (isLoading) {
      return <tr><td colSpan="5" className="text-center p-4">Loading jobs...</td></tr>;
    }

    if (error) {
      return <tr><td colSpan="5" className="text-center p-4 text-red-500">{error}</td></tr>;
    }

    if (jobs.length === 0) {
      return <tr><td colSpan="5" className="text-center p-4 text-gray-500">No backup jobs found. Run the Naruto agent to see data here.</td></tr>;
    }

    return jobs.map((job) => (
      <tr key={job.id} className="hover:bg-gray-50">
        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{job.job_id}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
            job.status === 'Completed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {job.status}
          </span>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{job.subclient}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(job.start_time).toLocaleString()}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{job.end_time ? new Date(job.end_time).toLocaleString() : 'N/A'}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
          {job.status.toLowerCase() !== 'completed' && (
            <Link 
              to={`/jobs/details/${job.id}`} 
              className="text-indigo-600 hover:text-indigo-900 font-semibold hover:underline"
            >
              Analyze
            </Link>
          )}
        </td>
      </tr>
    ));
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
        <AlertsSummary />
        <p className="text-gray-500 mt-1">
          Welcome back, {user?.email}! Here's a real-time overview of your backup environment.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-700">Recent Backup Jobs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subclient</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {renderTableContent()}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;