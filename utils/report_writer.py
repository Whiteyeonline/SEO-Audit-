# utils/report_writer.py

import json
from jinja2 import Environment, FileSystemLoader
import datetime 

def calculate_seo_score(report_data):
    """Calculates a final SEO score based on penalties applied to check results."""
    score = 100
    PENALTIES = {
        'ssl_fail': 20, 'robots_fail': 10, 'performance_fail': 15,
        'meta_desc_fail_per_page': 1, 'h1_fail_per_page': 0.5,
    }
    
    # 1. Basic Checks
    ssl_status = report_data.get('basic_checks', {}).get('ssl_check', {}).get('result', 'Fail')
    robots_status = report_data.get('basic_checks', {}).get('robots_sitemap', {}).get('status', 'Fail')
    
    if ssl_status != 'Pass':
        score -= PENALTIES['ssl_fail']
    if robots_status == 'Fail':
        score -= PENALTIES['robots_fail']

    # 2. Performance Check (Internal)
    performance_check = report_data.get('performance_check', {})
    desktop_result = performance_check.get('desktop_score', {}).get('result', 'Fail')
    
    if desktop_result == 'Fail':
        score -= PENALTIES['performance_fail']

    # 3. Crawled Page Penalties
    crawled_pages = report_data.get('crawled_pages', [])
    
    for page in crawled_pages:
        # Penalize for missing Meta Description
        if not page.get('meta', {}).get('description'):
            score -= PENALTIES['meta_desc_fail_per_page']
            
        # Penalize for bad H1 count
        if page.get('headings', {}).get('h1') != 1:
            score -= PENALTIES['h1_fail_per_page']

    return max(0, score)


def write_summary_report(report, json_path, md_path, audit_level):
    """Writes the final report data to both JSON and Markdown files."""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
        
    env = Environment(loader=FileSystemLoader('reports'))
    env.globals.update(now=lambda: datetime.datetime.now())
    template = env.get_template('template.md.j2')

    output = template.render(report=report)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Report written to {json_path} and {md_path}")
