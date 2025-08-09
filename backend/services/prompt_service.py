# backend/services/prompt_service.py

def get_triage_prompt(failure_summary: str, formatted_events: str) -> str:
    """Generates the prompt for the initial AI triage."""
    return f"""
    You are a Commvault Triage Expert. Analyze the following data from a failed backup job.
    Your task is to decide if you have enough information for a root cause analysis or if more logs are needed.

    DATA:
    - Failure Summary: "{failure_summary}"
    - Final Job Events: "{formatted_events}"

    CRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object. Do not include any introductory text, explanations, or code formatting like ```json. Your entire response must be a single JSON object.

    First, decide if the data is sufficient. If the summary or events are specific (e.g., "insufficient free space", "network timeout", "credentials failed"), the information IS sufficient. If both are generic (e.g., "backup failed"), you NEED more logs.

    Then, construct your JSON response based on one of the two following examples.

    EXAMPLE 1: If information IS sufficient:
    {{
      "is_sufficient": true,
      "logs_needed": [],
      "analysis": {{
        "problem_summary": "The backup failed due to insufficient disk space on the MediaAgent.",
        "probable_cause": "The DDB snapshot could not be created because the volume group 'vgnrm1' did not have enough free extents.",
        "recommended_action": "The storage administrator needs to extend the 'vgnrm1' volume group on the MediaAgent to free up space for DDB snapshots."
      }}
    }}

    EXAMPLE 2: If information is NOT sufficient:
    {{
      "is_sufficient": false,
      "logs_needed": ["JobManager.log"],
      "analysis": null
    }}
    """

def get_triage_prompt_test(failure_summary: str, formatted_events: str) -> str:
    """Generates the prompt for the initial AI triage."""
    return f"""
    You are a Commvault Triage Expert acting in a system testing capacity.
    Your current objective is to test the system's ability to fetch detailed logs.
    Therefore, for this specific request, you must always decide that the initial information is insufficient, even if it appears to be specific and complete.

    DATA:
    - Failure Summary: "{failure_summary}"
    - Final Job Events: "{formatted_events}"

    CRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object. Do not include any introductory text or explanations. Your entire response must be a single JSON object.

    Based on your objective to test the log fetching system, construct your JSON response to match the following example perfectly.

    EXAMPLE RESPONSE (USE THIS FORMAT):
    {{
      "is_sufficient": false,
      "logs_needed": ["JobManager.log"],
      "analysis": null
    }}
    """

def get_deep_analysis_prompt(initial_data: dict, log_data: dict) -> str:
    """Generates the prompt for the final, deep-dive AI analysis."""
    failure_summary = initial_data.get('failure_summary', 'N/A')
    events = initial_data.get('events', [])
    formatted_logs = "\n".join([f"{log_name}:\n{content}" for log_name, content in log_data.items()])

    return f"""
    You are a Commvault Root Cause Analysis Expert. You have the following comprehensive information for a failed backup job.

    Initial Triage Data:
    - Failure Summary: {failure_summary}
    - Final Job Events: {events}

    Detailed Log Snippets from requested files:
    ---
    {formatted_logs}
    ---

    Based on ALL of this combined information, provide the final, definitive analysis.
    Respond ONLY in JSON format with three keys: "problem_summary", "probable_cause", and "recommended_action".
    """