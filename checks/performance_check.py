# checks/performance_check.py (INTERNAL CHECK ONLY)

import requests
import time
import os
import json # Kept for consistency, though not strictly needed for this simple check

# --- Utility Function for Safe Extraction (Now unused, but kept simple for future) ---
def extract_score(data):
    """Placeholder function for a more complex check."""
    return data

# --- Main Check Function ---
def run_pagespeed_check(url):
    """
    Replaced PageSpeed API call with a free, internal Server Response Time check.
    """
    
    response_time = 0.0
    # Use standard requests, no Playwright needed for this check
    try:
        start_time = time.time()
        
        # Make a HEAD request for speed, or GET request for full test
        response = requests.get(url, timeout=10) 
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2) # Time in milliseconds
        
        if response_time < 500:
            result = 'Pass'
            message = f"Excellent: Response time is {response_time}ms."
        elif response_time < 1500:
            result = 'Warning'
            message = f"Acceptable: Response time is {response_time}ms. Needs optimization."
        else:
            result = 'Fail'
            message = f"Poor: Response time is {response_time}ms. High priority to optimize."
            
        status = response.status_code
            
    except requests.exceptions.RequestException as e:
        status = 500
        result = 'Fail'
        message = f"Connection error or timeout: {e}"

    # Return structure matching the old API format for report consistency
    return {
        'check_name': 'Server Response Time (Internal Check)',
        'target_url': url,
        # We use the same keys but provide internal data
        'mobile_score': {'result': result, 'score': max(0, 100 - int(response_time/50)), 'message': message}, 
        'desktop_score': {'result': result, 'score': max(0, 100 - int(response_time/50)), 'message': message},
        'response_time_ms': response_time,
        'http_status': status,
        'status': 'Complete'
    }
    
