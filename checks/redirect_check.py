# checks/redirect_check.py

"""
Redirect Check Module
Logs information if the page was a result of a redirect.
"""

def run_check(response, page_data, report_data):
    """
    Runs the Redirect check on the given response.
    Note: This check is often more effective if implemented within the
    Scrapy middleware to capture the full redirect chain. This simple check 
    detects if the final response URL differs from the initial request URL.
    """
    check_name = "redirect_check"
    report_data[check_name] = {
        "status": "PASS",
        "description": "Checks if the final page URL is the same as the initial request URL (no unexpected redirects).",
        "details": [],
        "score_impact": 0
    }

    # Check if the URL after following the request is different from the original
    if response.url != response.request.url:
        report_data[check_name]['status'] = "INFO"
        report_data[check_name]['score_impact'] = 0 # No direct score impact, but important info
        report_data[check_name]['details'].append(
            f"The request to '{response.request.url}' was redirected to '{response.url}'. "
            "Inspect redirects for potential SEO issues (e.g., redirect chains, non-301/302 status)."
        )
    else:
        report_data[check_name]['details'].append(
            "No redirect detected between the initial request and the final response URL."
        )
        
    return report_data
  
