# checks/__init__.py
# This file must explicitly list all module names so they can be imported 
# directly from the 'checks' package (e.g., from checks import ssl_check).

# Core Infrastructure/Technical Checks
from . import ssl_check
from . import robots_sitemap
from . import performance_check
from . import url_structure
from . import canonical_check
from . import link_check
from . import internal_links

# On-Page Element Checks
from . import meta_check
from . import heading_check
from . import image_check
from . import schema_check

# Content Quality & Keyword Checks
from . import keyword_analysis
from . import content_quality

# Specialized/Miscellaneous Checks
from . import accessibility_check
from . import mobile_friendly_check
from . import analytics_check
from . import backlinks_check
from . import local_seo_check 
