# checks/__init__.py

# Core Technical Checks
from . import ssl_check
from . import robots_sitemap
from . import url_structure
from . import canonical_check

# On-Page Element Checks
from . import meta_check
from . import heading_check
from . import image_check
from . import link_check
from . import internal_links

# Advanced Content & Performance Checks
from . import performance_check
from . import keyword_analysis
from . import content_quality
from . import schema_check

# Specialized/Miscellaneous Checks
from . import accessibility_check
from . import mobile_friendly_check
from . import analytics_check
from . import backlinks_check
from . import local_seo_check # Uses the correct file name: checks/local_seo_check.py
