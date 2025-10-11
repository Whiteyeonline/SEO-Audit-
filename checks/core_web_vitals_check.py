# checks/core_web_vitals_check.py

"""
Core Web Vitals Check Module
Provides a basic performance metric (TTFB) and suggests integrating a CWV API.
"""

def run_check(response, page_data, report_data):
    """
    Runs a simplified performance check related to Core Web Vitals (e.g., TTFB).
    """
    check_name = "core_web_vitals_check"
    report_data[check_name] = {
        "status": "INFO",
        "description": "Provides basic performance data and highlights the importance of Core Web Vitals.",
        "details": [],
        "score_impact": 0
    }

    # === Simplified Performance Check: Time To First Byte (TTFB) ===
    # Scrapy stores the time elapsed until headers are received in the response's metadata.
    # This is a proxy for TTFB.
    download_latency = response.meta.get('download_latency')

    if download_latency is not None:
        report_data[check_name]['details'].append(
            f"Download Latency (Proxy for TTFB): {download_latency:.3f} seconds."
        )

        # Basic threshold example: TTFB should be fast (under 0.6 seconds is generally good)
        if download_latency > 1.0:
            report_data[check_name]['status'] = "WARN"
            report_data[check_name]['score_impact'] = -10
            report_data[check_name]['details'].append(
                "WARNING: High Download Latency suggests a slow Time To First Byte (TTFB), "
                "which negatively impacts loading speed and CWV."
            )
        elif download_latency > 0.6:
            report_data[check_name]['status'] = "INFO"
            report_data[check_name]['details'].append(
                "INFO: Download Latency is acceptable, but review for further optimization."
            )
        else:
            report_data[check_name]['status'] = "PASS"
            report_data[check_name]['details'].append(
                "PASS: Download Latency is fast, indicating a good server response time."
            )
            
    # Add a note about true CWV
    report_data[check_name]['details'].append(
        "NOTE: For true Core Web Vitals (LCP, FID, CLS), consider integrating with "
        "a dedicated service like the Google PageSpeed Insights API."
    )
        
    return report_data
          
