# checks/__init__.py 
# This file initializes the checks module and makes all check files available via the parent 'checks' namespace.

from . import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis, 
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check,
    # === NEW CHECKS ADDED ===
    og_tags_check, 
    redirect_check, 
    core_web_vitals_check
)
