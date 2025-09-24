import ssl, socket
def run(url, html_content=None):
    try:
        domain = url.split("//")[-1].split("/")[0]
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            return {"valid_ssl": True, "issuer": cert.get("issuer", [])}
    except:
        return {"valid_ssl": False, "issuer": None}
      
