// src/pages/JobDetailsPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getJobById, createAnalysisTask, getTaskResult } from '../services/api'; 
import AnalysisStatus from '../components/AnalysisStatus';
import AIAnalysisResult from '../components/AIAnalysisResult';

function JobDetailsPage() {
  const { jobId } = useParams();

  const [job, setJob] = useState(null);
  const [task, setTask] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState(null);
  const [pollingError, setPollingError] = useState(null);

  useEffect(() => {
    const startAnalysisWorkflow = async () => {
      try {
        setIsInitializing(true);
        setError(null);

        const jobResponse = await getJobById(jobId);
        setJob(jobResponse.data);

        const taskResponse = await createAnalysisTask(jobId);
        setTask(taskResponse.data);

      } catch (err) {
        console.error("Failed to start analysis workflow:", err);
        setError(err.response?.data?.detail || "An error occurred.");
      } finally {
        setIsInitializing(false);
      }
    };

    startAnalysisWorkflow();
  }, [jobId]);

  // Polling useEffect
  useEffect(() => {
    if (!task || task.status === 'finalized' || task.status === 'failed') {
      return;
    }

    // Set up an interval to call the API every 4 seconds (a good polling interval)
    const intervalId = setInterval(async () => {
      try {
        setPollingError(null);
        console.log(`Polling for task ID: ${task.id}, current status: ${task.status}`);
        const response = await getTaskResult(task.id);
        setTask(response.data);
      } catch (err) {
        console.error("Polling failed:", err);
        setPollingError("Connection to the server was lost. Retrying..."); 
      }
    }, 7000);

    return () => clearInterval(intervalId);

  }, [task]);

  if (isInitializing) {
    return <div className="text-center p-8">Initializing analysis...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <strong className="font-bold">Error:</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">
        Analysis for Commvault Job ID: <span className="font-mono text-indigo-600">{job?.job_id}</span>
      </h1>
      
      {/* Display basic job info we fetched initially */}
      <div className="mb-6 border-b pb-4">
        <p><strong>Status:</strong> {job?.status}</p>
        <p><strong>Subclient:</strong> {job?.subclient}</p>
        <p><strong>Start Time:</strong> {job ? new Date(job.start_time).toLocaleString() : '...'}</p>
      </div>

      <div className="analysis-section mt-6">
        <h2 className="text-xl font-semibold mb-4 border-t pt-4">Analysis Status</h2>
        
        <div className="p-4 bg-gray-50 rounded-lg">
          <AnalysisStatus task={task} pollingError={pollingError} />
        </div>
        <AIAnalysisResult task={task} />
      </div>

      <div className="mt-6">
        <Link to="/" className="text-indigo-600 hover:underline">
          &larr; Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

export default JobDetailsPage;