import ssl, socket
import requests

def run(url, html_content=None):
    """
    Checks the SSL certificate status of the domain.
    Uses raw socket check first, then falls back to a requests check.
    """
    # Extract the base domain from the full URL
    domain = url.split("//")[-1].split("/")[0]
    
    # --- Primary Check: Raw Socket SSL ---
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10)
            s.connect((domain,443))
            cert = s.getpeercert()
            # Success
            return {"valid_ssl": True, "issuer": cert.get("issuer",[])}
    
    except Exception as e:
        socket_error = str(e)
        
        # --- Fallback Check: Requests ---
        # Some certificates/servers fail the raw socket check but work fine via HTTP libraries.
        try:
            r = requests.get(f"https://{domain}", timeout=10)
            r.raise_for_status() # Raises HTTPError for 4xx/5xx status codes
            
            # If requests succeeds without an exception, the SSL is valid for HTTPS traffic.
            return {"valid_ssl": True, "issuer": "requests verified"}
            
        except Exception as e2:
            # Failure
            return {
                "valid_ssl": False,
                "issuer": None,
                # Report both errors for transparency
                "error": f"socket error: {socket_error}, requests error: {str(e2)}"
        }
            
