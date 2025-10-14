# checks/performance_check.py

import requests
import time
import os
import json 
# Scrapy response object is passed in, but the requests library is used for timing

# FIX: The main function name is now 'run_audit' and accepts Scrapy arguments
def run_audit(response, audit_level):
    """
    Runs a free, internal Server Response Time check (replaces PageSpeed API)
    using the requests library to measure the time taken to fetch the URL.
    """
    
    # Use the URL from the Scrapy response object
    url = response.url 
    response_time = 0.0
    
    try:
        start_time = time.time()
        
        # Use simple GET request for full connection time
        # NOTE: Using a different library (requests) to avoid Scrapy's overhead in measurement
        response_check = requests.get(url, timeout=10) 
        
        end_time = time.time()
        # Time in milliseconds, rounded to 2 decimal places
        response_time = round((end_time - start_time) * 1000, 2)
        
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
            
        http_status = response_check.status_code
            
    except requests.exceptions.RequestException as e:
        http_status = 0
        result = 'Fail'
        score = 0
        message = f"Connection error or timeout during performance check: {e}"

    # The audit_level argument is mandatory but not used in this specific check.
    return {
        'check_name': 'Server Response Time (Internal Check)',
        'target_url': url,
        # Using the same result for both mobile/desktop since this is a server-side metric
        'mobile_score': {'result': result, 'score': score, 'message': message}, 
        'desktop_score': {'result': result, 'score': score, 'message': message},
        'response_time_ms': response_time,
        'http_status': http_status,
        'status': result
    }
    
