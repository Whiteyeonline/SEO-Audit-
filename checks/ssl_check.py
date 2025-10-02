import ssl, socket
import requests

def run(url, html_content=None):
    domain = url.split("//")[-1].split("/")[0]
    # Try raw socket SSL
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10)
            s.connect((domain,443))
            cert = s.getpeercert()
            return {"valid_ssl": True, "issuer": cert.get("issuer",[])}
    except Exception as e:
        # Try requests as a fallback
        try:
            r = requests.get(f"https://{domain}", timeout=10)
            r.raise_for_status()
            return {"valid_ssl": True, "issuer": "requests verified"}
        except Exception as e2:
            # Log both errors for transparency
            return {
                "valid_ssl": False,
                "issuer": None,
                "error": f"socket error: {str(e)}, requests error: {str(e2)}"
            }
