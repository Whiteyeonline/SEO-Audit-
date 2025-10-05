# utils/report_writer.py (Focus on calculate_seo_score)

import json
from jinja2 import Environment, FileSystemLoader
# You might need to import os here if your full file uses it

def calculate_seo_score(report_data):
    """
    Calculates a final SEO score based on penalties applied to check results.
    """
    score = 100
    
    # Define simple penalties
    PENALTIES = {
        'ssl_fail': 20,
        'robots_fail': 10,
        'performance_fail': 15,
        'meta_desc_fail_per_page': 1,
        'h1_fail_per_page': 0.5,
    }
    
    # --- Check 1: SSL Check (High Penalty) ---
    # FIX: Use .get() with a safe default value ({'result': 'Fail'}) if 'ssl_check' is missing 
    # or if the entire 'basic_checks' block is missing.
    ssl_check_result = report_data.get('basic_checks', {}).get('ssl_check', {})
    
    # SAFELY retrieve 'result'. Default to 'Fail' if the key is missing to apply the penalty.
    ssl_status = ssl_check_result.get('result', 'Fail')
    
    if ssl_status != 'Pass':
        score -= PENALTIES['ssl_fail']

    # --- Check 2: Robots/Sitemap Check (Medium Penalty) ---
    robots_check_result = report_data.get('basic_checks', {}).get('robots_sitemap', {})
    robots_status = robots_check_result.get('status', 'Fail')
    
    if robots_status == 'Fail':
        score -= PENALTIES['robots_fail']

    # --- Check 3: Performance Check (Based on PageSpeed) ---
    performance_check = report_data.get('performance_check', {})
    # Safely get the result, default to 'Fail' if the structure is missing
    desktop_result = performance_check.get('desktop_score', {}).get('result', 'Fail')
    
    if desktop_result == 'Fail':
        score -= PENALTIES['performance_fail']

    # --- Check 4: Aggregation of Crawled Page Issues (Iterative Penalty) ---
    crawled_pages = report_data.get('crawled_pages', [])
    
    for page in crawled_pages:
        # Penalize for missing Meta Description
        meta_desc = page.get('meta', {}).get('description')
        if not meta_desc:
            score -= PENALTies['meta_desc_fail_per_page']
            
        # Penalize for bad H1 count (assuming 0 or >1 is bad)
        h1_count = page.get('headings', {}).get('h1')
        if h1_count != 1:
            score -= PENALTIES['h1_fail_per_page']

    # --- Final Score ---
    final_score = max(0, score)
    return final_score


def write_summary_report(report, json_path, md_path, audit_level):
    """
    Writes the final report data to both JSON and Markdown files.
    """
    # Write JSON report
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
        
    # Write Markdown report
    env = Environment(loader=FileSystemLoader('reports'))
    env.globals.update(now=lambda: datetime.datetime.now())
    template = env.get_template('template.md.j2')

    # Render template with report data
    output = template.render(report=report)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Report written to {json_path} and {md_path}")
    
