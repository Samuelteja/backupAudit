# backend/services/ai_service.py

import os
import requests
from fastapi import HTTPException
import logging
import json

# Use the standard logging library for better output control
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
API_KEY = os.getenv("PERPLEXITY_API_KEY")

# It's good practice to have a timeout for external API calls
# to prevent your application from hanging indefinitely.
REQUEST_TIMEOUT_SECONDS = 60 


DEFAULT_SYSTEM_PROMPT = """
You are an expert Commvault Backup Administrator and Virtualization Specialist.
Your role is to analyze technical data from a backup environment and provide clear,
concise, and actionable insights for an IT administrator. Respond in the requested format.
"""

def get_perplexity_analysis(
    prompt: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = "sonar"
) -> str:
    """
    Sends a prompt to the Perplexity API and returns the AI's response.

    Args:
        prompt: The fully-formed user question/prompt to send to the AI.
        system_prompt: The context/role for the AI. Defaults to a Commvault expert.
        model: The specific Perplexity model to use.

    Returns:
        A string containing the content of the AI's response.

    Raises:
        HTTPException: For configuration errors, API failures, or timeouts.
    """

    # 1. Security & Configuration Check (moved to the top for a fail-fast approach)
    if not API_KEY:
        logger.error("CRITICAL: PERPLEXITY_API_KEY environment variable is not set.")
        raise HTTPException(status_code=500, detail="AI service is not configured.")

    # 2. Define Headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 3. Construct Payload
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        # Add optional parameters for better control over the output
        "temperature": 0.3, # Lower temperature for more deterministic, factual answers
        "max_tokens": 1024, # Prevent overly long responses
    }

    logger.info(f"Sending request to Perplexity API with model: {model}")

    try:
        # 4. Make the HTTP POST request with a timeout
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        # 5. Advanced Error Handling
        response.raise_for_status()

        response_data = response.json()
        
        choice = response_data.get("choices", [{}])[0]
        message = choice.get("message", {})
        ai_content = message.get("content")

        if not ai_content:
            logger.warning("Perplexity API returned a successful response with no content.")
            raise HTTPException(status_code=500, detail="AI service returned an empty response.")
        
        logger.info("Successfully received and parsed response from Perplexity API.")
        return ai_content

    except requests.exceptions.Timeout:
        logger.error(f"Request to Perplexity API timed out after {REQUEST_TIMEOUT_SECONDS} seconds.")
        raise HTTPException(status_code=504, detail="AI service timed out.")

    except requests.exceptions.HTTPError as e:
        # Log the detailed error from the API for easier debugging
        logger.error(f"Perplexity API returned an HTTP error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=502, detail=f"AI service failed with status code: {e.response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to Perplexity API: {e}")
        raise HTTPException(status_code=503, detail="The AI service is currently unavailable.")
        
    except (KeyError, IndexError) as e:
        logger.error(f"Could not parse Perplexity API response. Unexpected format: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI service response.")
    
def get_structured_ai_analysis(
    prompt: str,
    system_prompt: str = "You are a helpful assistant that only responds in valid JSON.",
    model: str = "sonar"
) -> dict:
    """
    Calls the Perplexity API, expects a JSON response, cleans it,
    and returns it as a Python dictionary.
    """
    raw_response_str = get_perplexity_analysis(prompt, system_prompt, model)
    

    try:
        start_index = raw_response_str.find('{')
        end_index = raw_response_str.rfind('}')
        
        if start_index != -1 and end_index != -1:
            json_str = raw_response_str[start_index : end_index + 1]
            return json.loads(json_str)
        else:
            logger.error(f"Could not find a valid JSON object in AI response: {raw_response_str}")
            raise ValueError("No JSON object found in AI response")
            
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse structured AI response: {e}")
        raise HTTPException(status_code=500, detail="AI service returned a non-parsable format.")