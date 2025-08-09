// src/components/AIAnalysisResult.jsx
import React from 'react';


const AnalysisSection = ({ title, children, icon }) => {
  // Only render the section if there's content to display
  if (!children || (Array.isArray(children) && children.length === 0)) {
    return null;
  }
  return (
    <div className="mb-6">
      <h3 className="flex items-center text-lg font-semibold text-gray-800 border-b-2 border-gray-200 pb-2 mb-3">
        <span className="mr-2">{icon}</span>
        {title}
      </h3>
      <div className="text-gray-700 prose prose-indigo max-w-none">
        {children}
      </div>
    </div>
  );
};

function AIAnalysisResult({ task }) {
  if (task?.status !== 'finalized' || !task.result?.ai_analysis) {
    return null;
  }

  const { problem_summary, probable_cause, recommended_action } = task.result.ai_analysis;

  return (
    <div className="mt-6 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
      <h2 className="text-xl font-bold text-gray-900 mb-4">AI-Powered Insight Report</h2>
      
      <AnalysisSection title="Problem Summary" icon="⚠️">
        <p>{problem_summary}</p>
      </AnalysisSection>

      <AnalysisSection title="Probable Cause Analysis" icon="🤔">
        <ul className="list-disc pl-5 space-y-1">
          {probable_cause.split('\n').map((line, index) => (
            line.trim() && <li key={index}>{line}</li> // Render only non-empty lines
          ))}
        </ul>
      </AnalysisSection>

      <AnalysisSection title="Recommended Next Steps" icon="➡️">
        <ol className="list-decimal pl-5 space-y-1">
           {recommended_action.split('\n').map((line, index) => (
            line.trim() && <li key={index}>{line}</li> // Render only non-empty lines
          ))}
        </ol>
      </AnalysisSection>
    </div>
  );
}

export default AIAnalysisResult;