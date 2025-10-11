# checks/redirect_check.py

def run_audit(response, audit_level):
    """
    Runs the Redirect check.
    Detects if the final response URL differs from the initial request URL.
    """
    
    was_redirected = False
    
    # Check if the final URL in the response is different from the original request URL
    # response.url is the final URL, response.request.url is the initially requested URL
    if response.url != response.request.url:
        was_redirected = True
        
    if was_redirected:
        note = f"INFO: The request to '{response.request.url}' was redirected to '{response.url}'. This suggests a redirect hop. Ensure it is a necessary 301/302."
    else:
        note = "PASS: No redirect detected. The requested URL is the final URL."
        
    return {
        "was_redirected": was_redirected,
        "initial_url": response.request.url,
        "final_url": response.url,
        "note": note
        }
    
