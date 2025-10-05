# checks/performance_check.py
import requests

PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedinsights/v5/runPagespeed"

def run_pagespeed_check(url):
    """Runs a check using the free Google PageSpeed Insights API."""
    
    # Run separate checks for Desktop and Mobile strategies
    desktop_params = {'url': url, 'strategy': 'desktop'}
    mobile_params = {'url': url, 'strategy': 'mobile'}
    
    def fetch_data(params):
        try:
            response = requests.get(PAGESPEED_API_URL, params=params, timeout=25)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"API request failed: {e}"}

    desktop_data = fetch_data(desktop_params)
    mobile_data = fetch_data(mobile_params)

    def extract_score(data):
        if 'error' in data:
            # Handle API errors gracefully
            return {'result': 'Fail', 'score': 0, 'message': data.get('error', {}).get('message', 'API request failed.')}
        
        # Performance Score (Lighthouse)
        score = data.get('lighthouseResult', {}).get('categories', {}).get('performance', {}).get('score', 0) * 100
        score = int(score)
        
        result = 'Pass'
        if score < 50:
            result = 'Fail'
        elif score < 90:
            result = 'Warning'
            
        return {'result': result, 'score': score, 'message': f"Lighthouse Performance Score: {score}"}

    return {
        'desktop_score': extract_score(desktop_data),
        'mobile_score': extract_score(mobile_data),
    }
    
