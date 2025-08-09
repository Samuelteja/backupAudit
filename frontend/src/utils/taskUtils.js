// src/utils/taskUtils.js

export const deriveTaskDisplayState = (task) => {
  if (!task) {
    return { status: 'initializing', message: 'Creating analysis task...' };
  }

  if (task.status === 'finalized') {
    return { status: 'success', message: 'Analysis Complete!' };
  }
  if (task.status === 'failed') {
    return { status: 'error', message: 'Analysis Failed. Check agent logs.' };
  }
  
  if (task.task_type === 'GET_JOB_DETAILS') {
    if (task.status === 'pending' || task.status === 'processing') {
      return { status: 'loading', message: 'Requesting initial details from on-premises agent...' };
    }

    if (task.status === 'complete') {
      const triageDecision = task.result?.triage_decision;

      if (!triageDecision) {
        return { status: 'loading', message: 'Initial data received. Performing AI triage...' };
      }

      if (triageDecision.is_sufficient === true) {
        // This is a brief state before it becomes 'finalized'
        return { status: 'loading', message: 'Triage complete. Finalizing analysis...' };
      }
      
      if (triageDecision.is_sufficient === false) {
        // Here, we need to know the status of the child task.
        // Since we don't have that info here, we can infer it.
        // The parent task will stay in this state until deep analysis is done.
        return { status: 'loading', message: 'Triage complete. Agent is now fetching detailed logs...' };
      }
    }
  }

  // Default fallback
  return { status: 'loading', message: 'Analysis in progress...' };
};