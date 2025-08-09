// src/components/AnalysisStatus.jsx
import React from 'react';
import { deriveTaskDisplayState } from '../utils/taskUtils'; // <-- IMPORT THE NEW HELPER

const Spinner = () => (
  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900 mr-3"></div>
);

function AnalysisStatus({ task, pollingError }) {
    if (pollingError) {
        return (
        <div className="flex items-center text-yellow-600 font-semibold">
            {/* Warning Icon */}
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.21 3.03-1.742 3.03H4.42c-1.532 0-2.492-1.696-1.742-3.03l5.58-9.92zM10 13a1 1 0 110-2 1 1 0 010 2zm-1-4a1 1 0 011-1h.008a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd"></path></svg>
            <span>{pollingError}</span>
        </div>
        );
    }
  const { status, message } = deriveTaskDisplayState(task);

  const getStatusClasses = () => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'loading':
      default:
        return 'text-blue-600';
    }
  };

  const getIcon = () => {
    switch(status) {
        case 'success':
            return <svg /* Checkmark Icon */ className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path></svg>;
        case 'error':
            return <svg /* X Icon */ className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>;
        case 'loading':
        default:
            return <Spinner />;
    }
  };

  return (
    <div className={`flex items-center font-semibold ${getStatusClasses()}`}>
      {getIcon()}
      <span>{message}</span>
    </div>
  );
}

export default AnalysisStatus;