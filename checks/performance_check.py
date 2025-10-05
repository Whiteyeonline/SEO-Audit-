# checks/performance_check.py

import requests
import json
import os # <--- CRITICAL FIX: Add the os module import
# ... (other potential imports like time, etc., should be here if needed)

# --- Utility Function for Safe Extraction ---
def extract_score(data):
    """Safely extracts performance score or handles API errors."""
    
    # CRITICAL FIX: Check if 'data' is a dictionary before using .get()
    if not isinstance(data, dict):
        # If it's not a dict, it's likely a raw string error message or None
        # Safely return a failure status
        return {'result': 'Fail', 'score': 0, 'message': 'API did not return valid JSON response.'}

    # Check for a specific API error structure
    if 'error' in data:
        return {'result': 'Fail', 'score': 0, 'message': data['error'].get('message', 'API request failed with unhandled error.')}

    # Extract performance metrics
    try:
        score_value = int(data
            .get('lighthouseResult', {})
            .get('categories', {})
            .get('performance', {})
            .get('score', 0) * 100) # Score is typically 0 to 1, convert to 0-100
            
        message = f"Score: {score_value}. See detailed Lighthouse report for metrics."
        result = 'Pass' if score_value >= 90 else ('Warning' if score_value >= 50 else 'Fail')
        
        return {'result': result, 'score': score_value, 'message': message}
    
    except Exception as e:
        return {'result': 'Fail', 'score': 0, 'message': f"Data extraction error: {e}"}


# --- Main Check Function ---
def run_pagespeed_check(url, api_key=None):
    """
    Runs Google PageSpeed Insights check for both mobile and desktop.
    """
    
    # This line now works because 'os' is imported at the top
    api_key = api_key or os.environ.get('GOOGLE_PAGESPEED_API_KEY')
    base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    # 1. Mobile Check
    mobile_params = {
        'url': url,
        'strategy': 'mobile',
        'locale': 'en_US',
        'key': api_key
    }
    
    try:
        mobile_response = requests.get(base_url, params=mobile_params, timeout=20)
        # Use .json() to parse the response, but handle the case where it might fail
        try:
            mobile_data = mobile_response.json()
        except json.JSONDecodeError:
            # If JSON decoding fails, the response content is likely the raw error string
            mobile_data = mobile_response.text 
            
    except requests.exceptions.RequestException as e:
        mobile_data = {'error': {'message': f"Request failed: {e}"}}


    # 2. Desktop Check
    desktop_params = {
        'url': url,
        'strategy': 'desktop',
        'locale': 'en_US',
        'key': api_key
    }
    
    try:
        desktop_response = requests.get(base_url, params=desktop_params, timeout=20)
        try:
            desktop_data = desktop_response.json()
        except json.JSONDecodeError:
            desktop_data = desktop_response.text
            
    except requests.exceptions.RequestException as e:
        desktop_data = {'error': {'message': f"Request failed: {e}"}}


    # 3. Compile Results
    return {
        'check_name': 'Performance Check (PageSpeed Insights)',
        'target_url': url,
        'mobile_score': extract_score(mobile_data),
        'desktop_score': extract_score(desktop_data),
        'status': 'Complete'
    }
    
