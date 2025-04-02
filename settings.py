# settings.py
import logging

# --- General Settings ---
OUTPUT_DIRECTORY = "console_errors"  # Folder to save the error log files
CRAWL_DELAY = 1  # Delay in seconds between crawling each page
CREATE_EMPTY_LOG_FILES = False  # If True, create a log file even for pages with no errors found. If False, skip creating files for pages with no errors.

# --- Script Logging Settings ---
# Level of detail for the script's own logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
SCRIPT_LOG_LEVEL = logging.INFO
SCRIPT_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# --- Requests Settings (for fetching sitemaps) ---
REQUESTS_USER_AGENT = 'BoostifyUSA-SitemapCrawler/1.0 (+http://yourwebsite.com/botinfo)' # Modify with your info URL if available
REQUESTS_TIMEOUT = 30  # Timeout in seconds for fetching sitemaps

# --- Selenium WebDriver Settings ---
SELENIUM_HEADLESS = True  # Run Chrome in headless mode (True) or with a visible window (False)
SELENIUM_DISABLE_GPU = True  # Disable GPU acceleration (often needed for headless)
SELENIUM_NO_SANDBOX = True  # Bypass OS security model (needed on some Linux systems)
SELENIUM_DISABLE_DEV_SHM_USAGE = True  # Overcome limited resource problems in Docker/Linux
SELENIUM_WINDOW_SIZE = "1920,1080"  # Initial window size (WxH)
SELENIUM_PAGE_LOAD_TIMEOUT = 60  # Max time in seconds to wait for a page to load
SELENIUM_SCRIPT_TIMEOUT = 30  # Max time in seconds to wait for async scripts
SELENIUM_DRIVER_LOG_LEVEL = '3' # Verbosity level for the ChromeDriver process itself (e.g., '0' for all, '3' for fatal)
SELENIUM_USER_AGENT = 'BoostifyUSA-SitemapCrawler/1.0 Selenium (+http://yourwebsite.com/botinfo)' # Modify with your info URL

# --- Browser Console Log Settings ---
# Log level to capture from the browser console. Options: 'SEVERE', 'WARNING', 'INFO', 'ALL'
# Note: Capturing lower levels (WARNING, INFO) can generate a LOT of data. 'SEVERE' usually captures JavaScript errors.
BROWSER_LOG_LEVEL = 'SEVERE'
# Optional: List of substrings. If a log message contains any of these (case-insensitive), it will be excluded.
# Example: FILTER_LOG_MESSAGES = ['favicon.ico', 'jquery-migrate']
FILTER_LOG_MESSAGES = []

# --- Sitemap Parsing ---
# Namespaces used for finding URLs in sitemap XML files
SITEMAP_NAMESPACES = {
    's': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    # Add other namespaces if your sitemaps use them (e.g., 'image:', 'video:')
}
SITEMAP_XML_RECOVER_MODE = True # Attempt to parse slightly malformed XML sitemaps