# checks/performance_check.py (Final, Corrected Function Name)

import requests
import time
import os
import json 

# CRITICAL FIX: The main function name is 'run'
def run(url):
    """
    Runs a free, internal Server Response Time check (replaces PageSpeed API).
    """
    
    response_time = 0.0
    
    try:
        start_time = time.time()
        
        # Use simple GET request for full connection time
        response = requests.get(url, timeout=10) 
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2) # Time in milliseconds
        
        # Scoring logic based on common industry standards
        if response_time < 500:
            result = 'Pass'
            score = 95
            message = f"Excellent: Server response time is {response_time}ms (Target: < 500ms)."
        elif response_time < 1500:
            result = 'Warning'
            score = 60
            message = f"Acceptable: Response time is {response_time}ms (Target: < 1500ms)."
        else:
            result = 'Fail'
            score = 30
            message = f"Poor: Response time is {response_time}ms. High priority to optimize."
            
        http_status = response.status_code
            
    except requests.exceptions.RequestException as e:
        http_status = 0
        result = 'Fail'
        score = 0
        message = f"Connection error or timeout during performance check: {e}"

    return {
        'check_name': 'Server Response Time (Internal Check)',
        'target_url': url,
        'mobile_score': {'result': result, 'score': score, 'message': message}, 
        'desktop_score': {'result': result, 'score': score, 'message': message},
        'response_time_ms': response_time,
        'http_status': http_status,
        'status': result
    }
    
