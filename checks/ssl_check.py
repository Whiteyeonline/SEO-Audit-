import ssl, socket
import requests
from urllib.parse import urlparse

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks the SSL certificate status of the domain using the response URL.
    Uses raw socket check first, then falls back to a requests check.
    
    The audit_level argument is mandatory but not used in this specific check.
    """
    # Use the response URL to get the base domain
    domain = urlparse(response.url).netloc
    
    # --- Primary Check: Raw Socket SSL ---
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10)
            s.connect((domain, 443))
            cert = s.getpeercert()
            
            # Success
            return {
                "valid_ssl": True, 
                "ssl_check_fail": False,
                "issuer": cert.get("issuer", [("organizationName", "N/A")])[0][1], # Extract org name
                "note": "SSL certificate is valid and connection was successful."
            }
    
    except Exception as e:
        socket_error = str(e)
        
        # --- Fallback Check: Requests ---
        try:
            # Use requests to verify if HTTPS connection is possible
            requests.get(response.url, timeout=10, verify=True)
            
            # If requests succeeds, the SSL is valid for HTTPS traffic, 
            # even if the raw socket failed (due to setup/environment differences).
            return {
                "valid_ssl": True, 
                "ssl_check_fail": False,
                "issuer": "Requests Verified",
                "note": "SSL is valid, confirmed via HTTPS request."
            }
            
        except Exception as e2:
            # Failure
            return {
                "valid_ssl": False,
                "ssl_check_fail": True,
                "issuer": None,
                "note": "Critical Failure: HTTPS connection failed (Certificate invalid or missing).",
                "error": f"socket error: {socket_error}, requests error: {str(e2)}"
            }
            
