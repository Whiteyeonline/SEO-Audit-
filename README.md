# 🚀 Simple One-Page SEO Audit Tool

This project provides a simple, two-step workflow for performing a one-page SEO audit. It is designed to be used on a local machine or as part of a GitHub Actions workflow.

### ⚙️ Workflow

The process consists of two main parts:

1.  **Data Collection (`main.py`)**: This script crawls a given URL, fetches on-page SEO data (like title tags, meta descriptions, headings, and links), and saves the results into a raw `seo_data.json` file.
    
    **How to use:**
    
    ```bash
    python main.py [https://your-website.com](https://your-website.com)
    ```
    
2.  **Report Generation (`report_generator.py`)**: This script reads the `seo_data.json` file and transforms the raw data into a human-readable, formatted SEO report in Markdown (`seo_report.md`). No external APIs or AI models are used for this step.
    
    **How to use:**
    
    ```bash
    python report_generator.py seo_data.json
    ```

### 📦 Setup

1.  **Clone the repository:**
    
    ```bash
    git clone [your-repo-url]
    cd [your-repo-name]
    ```
    
2.  **Install dependencies:**
    
    ```bash
    pip install -r requirements.txt
    ```
    
3.  **Run the audit:**
    
    Follow the workflow steps above to generate your report.

### 📝 Files

* `main.py`: The script for crawling a URL and collecting raw SEO data.
* `report_generator.py`: The script for transforming the raw data into a formatted report.
* `requirements.txt`: The list of Python dependencies required for the project.
* `README.md`: This file.
