# utils/report_writer.py
import json
from jinja2 import Environment, FileSystemLoader

# ... (keep calculate_seo_score function logic here) ...
def calculate_seo_score(report_data):
    """Calculate a simple weighted SEO score based on check results."""
    
    total_score = 100
    deduction = 0
    
    # Simple Deduction Logic (adjust weights as needed)
    
    # 1. Basic Checks
    if report_data['basic_checks']['ssl_check']['result'] != 'Pass':
        deduction += 10 # Critical
    if report_data['basic_checks']['robots_sitemap']['result'] != 'Pass':
        deduction += 5
        
    # 2. Performance Check
    if report_data['performance_check']['mobile_score']['result'] == 'Fail':
        deduction += 10
        
    # 3. Crawled Page Analysis (Average deduction)
    if 'crawled_pages' in report_data and report_data['crawled_pages']:
        page_deduction = 0
        for page in report_data['crawled_pages']:
            if not page.get('title'): page_deduction += 2
            if not page.get('meta_description'): page_deduction += 2
            
            # Deduct for Keyword Stuffing warning
            if page.get('keyword_analysis', {}).get('density_check', {}).get('result') == 'Warning':
                page_deduction += 1
                
        # Average the deduction across all pages (max 30 points from page checks)
        avg_deduction = (page_deduction / len(report_data['crawled_pages']))
        deduction += min(avg_deduction, 30) # Capped at 30 points
        
    final_score = max(0, total_score - int(deduction))
    return f"{final_score}/100"


def write_summary_report(data, json_path, md_path, audit_level):
    """Writes the structured data to both JSON and a consistent Markdown report using Jinja2."""

    # 1. Write JSON file (The Single Source of Truth)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # 2. Setup Jinja2 Environment
    try:
        # Load environment with current directory as the loader (assuming 'reports' is a sibling to utils)
        # You may need to adjust the path if your 'reports' directory is elsewhere.
        file_loader = FileSystemLoader('reports') 
        env = Environment(loader=file_loader)
        # Add the 'now' function to the template environment for date
        from datetime import datetime
        env.globals.update(now=datetime.now)
        
        template = env.get_template('template.md.j2')
    except Exception as e:
        print(f"Error loading Jinja2 template: {e}. Cannot generate Markdown report.")
        return

    # 3. Render the Markdown report from the JSON data
    # The template directly accesses fields from the `data` dictionary (the JSON content)
    output = template.render(report=data, audit_level=audit_level)

    # 4. Write the final Markdown report
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(output)
        
