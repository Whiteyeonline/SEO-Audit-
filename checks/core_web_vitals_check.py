# checks/core_web_vitals_check.py

def run_audit(response, audit_level):
    """
    Runs a simplified performance check related to Core Web Vitals (e.g., TTFB proxy).
    
    This check relies on Scrapy's download latency, a proxy for TTFB, and does 
    not require HTML parsing.
    """
    
    # Scrapy stores the time elapsed until headers are received in the response's metadata.
    # This is a good proxy for Time To First Byte (TTFB).
    download_latency = response.meta.get('download_latency')
    
    performance_status = "INFO"
    note = "Could not determine download latency."
    
    if download_latency is not None:
        
        # TTFB threshold: < 0.6s is often considered green for CWV
        if download_latency > 1.0:
            performance_status = "⚠️ WARN"
            note = f"WARNING: High Download Latency ({download_latency:.3f}s) suggests a slow Time To First Byte (TTFB), which negatively impacts loading speed and CWV."
        elif download_latency > 0.6:
            performance_status = "INFO"
            note = f"INFO: Download Latency ({download_latency:.3f}s) is acceptable, but review for further optimization."
        else:
            performance_status = "✅ PASS"
            note = f"PASS: Download Latency ({download_latency:.3f}s) is fast, indicating a good server response time."

    note += " NOTE: For true Core Web Vitals (LCP, FID, CLS), consider integrating with a dedicated service like Google PageSpeed Insights API."

    return {
        "download_latency": download_latency,
        "performance_status": performance_status,
        "note": note
    }
    
