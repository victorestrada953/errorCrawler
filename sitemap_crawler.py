# -*- coding: utf-8 -*-
"""
Sitemap URL Crawler and Console Error Logger

This script takes a WordPress sitemap URL (index or standard),
extracts all page URLs, crawls each page using a headless browser (Selenium),
and logs any severe JavaScript console errors found to separate files.

Author: Boostify USA
Date:   07/22/2024
License: MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import requests
import time
import os
import re
import logging
from lxml import etree
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException

# --- Import Configuration ---
try:
    import settings
except ImportError:
    print("ERROR: settings.py not found. Please ensure it exists in the same directory.")
    exit()
# --- End Import ---


# --- Configure Logging (from settings) ---
# Note: Use today's date (April 2, 2025) or keep the original date based on intent.
# Using original date for consistency with header unless specified otherwise.
logging.basicConfig(level=settings.SCRIPT_LOG_LEVEL, format=settings.SCRIPT_LOG_FORMAT)
# --- End Logging Configuration ---


def sanitize_filename(url):
    """Creates a safe filename from a URL."""
    if not url:
        return "invalid_url"
    # Remove scheme
    parsed_url = urlparse(url)
    # Handle cases where netloc might be empty (e.g., "mailto:" links, though unlikely in sitemaps)
    netloc = parsed_url.netloc if parsed_url.netloc else ''
    path_part = parsed_url.path if parsed_url.path else ''
    path = netloc + path_part
    # Remove trailing slash if it's the only thing in the path
    if path.endswith('/') and len(path) > 1:
        path = path[:-1]
    # Replace invalid filename characters with underscores
    # Handles Windows and Linux/macOS invalid chars
    safe_name = re.sub(r'[\\/*?:"<>|\x00-\x1f]', '_', path)
    # Replace remaining slashes with underscores for flatter structure
    safe_name = safe_name.replace('/', '_')
    # Remove leading/trailing underscores/dots that might cause issues
    safe_name = safe_name.strip('._')
    # Truncate if too long (OS limits vary, 200 is generally safe)
    max_len = 200
    if len(safe_name) > max_len:
        # Find last underscore before max_len for cleaner cut if possible
        cut_point = safe_name.rfind('_', 0, max_len)
        if cut_point != -1:
             safe_name = safe_name[:cut_point]
        else:
             safe_name = safe_name[:max_len]

    # Ensure filename is not empty after sanitization and doesn't potentially clash with reserved names
    if not safe_name or safe_name.upper() in ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']:
        # Fallback for empty or reserved names - maybe use hash or counter? Simple fallback for now.
        safe_name = f"sanitized_url_{abs(hash(url))}"

    return f"{safe_name}.log"


def get_all_page_urls(sitemap_url, visited_sitemaps=None):
    """
    Recursively fetches and parses sitemaps (index or regular)
    and returns a set of all unique page URLs found. Uses settings from settings.py
    """
    if visited_sitemaps is None:
        visited_sitemaps = set()

    if sitemap_url in visited_sitemaps:
        logging.warning(f"Sitemap already visited, skipping: {sitemap_url}")
        return set()

    visited_sitemaps.add(sitemap_url)
    page_urls = set()
    # Use User-Agent from settings
    headers = {'User-Agent': settings.REQUESTS_USER_AGENT}

    try:
        logging.info(f"Fetching sitemap: {sitemap_url}")
        # Use timeout from settings
        response = requests.get(sitemap_url, headers=headers, timeout=settings.REQUESTS_TIMEOUT)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        content = response.content
        if not content:
            logging.warning(f"Sitemap is empty: {sitemap_url}")
            return set()

        # Use recover mode from settings
        parser = etree.XMLParser(recover=settings.SITEMAP_XML_RECOVER_MODE, remove_blank_text=True)
        root = etree.fromstring(content, parser=parser)

        # Check if root element exists (parsing might recover but result in None)
        if root is None:
             logging.error(f"Failed to parse XML structure correctly (root is None) for: {sitemap_url}")
             return set()

        # Use namespaces from settings
        sitemap_ns = settings.SITEMAP_NAMESPACES

        # Make tag checking more robust against default namespace variations
        tag_name = etree.QName(root.tag).localname

        # Check if it's a sitemap index file
        if tag_name == 'sitemapindex':
            logging.info(f"Detected sitemap index: {sitemap_url}")
            # Use explicit namespace in XPath for reliability
            sitemaps = root.xpath('.//s:sitemap/s:loc/text() | .//default:sitemap/default:loc/text()',
                                 namespaces={'s': sitemap_ns.get('s', ''), 'default': sitemap_ns.get('s', '')})
            for sub_sitemap_url in sitemaps:
                absolute_sub_url = urljoin(sitemap_url, sub_sitemap_url.strip())
                page_urls.update(get_all_page_urls(absolute_sub_url, visited_sitemaps))

        # Check if it's a URL set file
        elif tag_name == 'urlset':
            logging.info(f"Detected URL set: {sitemap_url}")
            # Use explicit namespace in XPath
            urls = root.xpath('.//s:url/s:loc/text() | .//default:url/default:loc/text()',
                             namespaces={'s': sitemap_ns.get('s', ''), 'default': sitemap_ns.get('s', '')})
            for page_url in urls:
                 url_text = page_url.strip()
                 if url_text.startswith('http://') or url_text.startswith('https://'):
                     page_urls.add(url_text)
                 else:
                     logging.warning(f"Skipping invalid/relative URL found in {sitemap_url}: {url_text}")
        else:
            logging.warning(f"Unknown sitemap format/root tag '{root.tag}' in: {sitemap_url}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch sitemap {sitemap_url}: {e}")
    except etree.XMLSyntaxError as e:
        logging.error(f"Failed to parse XML sitemap {sitemap_url}: {e}")
    except Exception as e:
        # Catching potential errors during urljoin or set updates etc.
        logging.error(f"An unexpected error occurred while processing {sitemap_url}: {e}", exc_info=True) # Include traceback

    return page_urls

def crawl_and_log_errors(urls_to_crawl):
    """
    Crawls each URL using Selenium, captures console errors based on settings.py,
    and saves them to individual files.
    """
    if not urls_to_crawl:
        logging.info("No URLs found to crawl.")
        return

    logging.info(f"Setting up Selenium WebDriver based on settings.py...")
    options = Options()

    # Apply Selenium options from settings
    if settings.SELENIUM_HEADLESS:
        options.add_argument("--headless")
    if settings.SELENIUM_DISABLE_GPU:
        options.add_argument("--disable-gpu")
    if settings.SELENIUM_NO_SANDBOX:
        options.add_argument("--no-sandbox")
    if settings.SELENIUM_DISABLE_DEV_SHM_USAGE:
        options.add_argument("--disable-dev-shm-usage")
    if settings.SELENIUM_WINDOW_SIZE:
        options.add_argument(f"--window-size={settings.SELENIUM_WINDOW_SIZE}")
    if settings.SELENIUM_DRIVER_LOG_LEVEL:
         # Valid Chrome log levels: INFO = 0, WARNING = 1, LOG_ERROR = 2, LOG_FATAL = 3. Default is 0.
         # Let's map Selenium Driver log level more verbosely if needed, or keep as is. Stick to arg for now.
         options.add_argument(f"--log-level={settings.SELENIUM_DRIVER_LOG_LEVEL}")
    if settings.SELENIUM_USER_AGENT:
        options.add_argument(f"user-agent={settings.SELENIUM_USER_AGENT}")

    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # Enable browser logging to capture console errors based on settings
    options.set_capability("goog:loggingPrefs", {"browser": settings.BROWSER_LOG_LEVEL.upper()}) # Ensure level is uppercase

    driver = None
    try:
        logging.info("Installing/Verifying ChromeDriver...")
        # Ensure the service object is properly defined
        try:
            service = Service(ChromeDriverManager().install())
            logging.info("ChromeDriver is up to date.")
        except Exception as driver_manager_err:
             logging.error(f"Failed to download/install ChromeDriver: {driver_manager_err}", exc_info=True)
             return # Cannot proceed without driver

        logging.info("Initializing WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)

        # Set timeouts from settings
        driver.set_page_load_timeout(settings.SELENIUM_PAGE_LOAD_TIMEOUT)
        # Implicit waits are generally discouraged with explicit waits, but setting script timeout is fine.
        driver.set_script_timeout(settings.SELENIUM_SCRIPT_TIMEOUT)

        logging.info("WebDriver setup complete.")

        # Use output directory from settings
        output_dir = settings.OUTPUT_DIRECTORY
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Saving error logs to directory: '{os.path.abspath(output_dir)}'")
        except OSError as dir_err:
            logging.error(f"Could not create output directory '{output_dir}': {dir_err}", exc_info=True)
            return # Cannot proceed without output directory

        total_urls = len(urls_to_crawl)
        logging.info(f"Starting crawl of {total_urls} URLs...")

        # Prepare lowercase filter list once
        filter_list = [str(f).lower() for f in settings.FILTER_LOG_MESSAGES] # Ensure filters are strings

        for i, url in enumerate(urls_to_crawl, 1):
            logging.info(f"Crawling URL {i}/{total_urls}: {url}")
            error_log_entries = []
            filename = sanitize_filename(url)
            filepath = os.path.join(output_dir, filename)

            try:
                driver.get(url)
                # Use crawl delay from settings
                if settings.CRAWL_DELAY > 0:
                    time.sleep(settings.CRAWL_DELAY)

                # Retrieve browser logs (already filtered by level via capabilities)
                try:
                    logs = driver.get_log('browser')
                except WebDriverException as log_err:
                     # Handle cases where logs might not be available (e.g., browser crashed)
                     logging.error(f"Could not retrieve browser logs for {url}: {log_err}")
                     logs = [] # Treat as no logs found

                # Process captured logs
                for entry in logs:
                    message = entry.get('message', 'No message content.')
                    message_lower = message.lower()

                    # Apply custom message filtering from settings
                    if filter_list and any(filter_text in message_lower for filter_text in filter_list):
                        continue # Skip this log entry if it matches a filter

                    # Format the message
                    timestamp_ms = entry.get('timestamp', time.time() * 1000)
                    timestamp_sec = timestamp_ms / 1000.0
                    # Handle potential timestamp errors
                    try:
                         log_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_sec))
                    except ValueError:
                         log_time = "Invalid Timestamp"
                    level = entry.get('level', 'UNKNOWN')
                    # Clean up potential WebDriver noise in message
                    # message = message.replace('\\n', '\n').replace('\\u003C', '<') # This might break JSON/structured messages
                    error_log_entries.append(f"[{log_time}] {level} - {message}")


                # Decide whether to save the file based on errors found and settings
                if not error_log_entries and not settings.CREATE_EMPTY_LOG_FILES:
                    logging.info(f"No relevant console errors ({settings.BROWSER_LOG_LEVEL}) found on {url}, skipping file creation.")
                    continue # Skip to the next URL

                # Save errors (or no errors message) to the specific file
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        if error_log_entries:
                            logging.warning(f"Found {len(error_log_entries)} relevant console log(s) (level {settings.BROWSER_LOG_LEVEL}+) on: {url}")
                            f.write(f"Console logs (level {settings.BROWSER_LOG_LEVEL}+) found on: {url}\n")
                            f.write("=" * 30 + "\n")
                            for error in error_log_entries:
                                f.write(error + "\n\n")
                        else:
                            # This part only runs if CREATE_EMPTY_LOG_FILES is True and no relevant logs were found
                            logging.info(f"No relevant console logs (level {settings.BROWSER_LOG_LEVEL}+) found on: {url}")
                            f.write(f"No relevant console logs (level {settings.BROWSER_LOG_LEVEL}+) found on: {url}\n")
                except OSError as write_err:
                     logging.error(f"Failed to write log file {filepath}: {write_err}")
                     # Optional: Decide if you want to stop the whole script on a write error

            except TimeoutException:
                 logging.error(f"Timeout loading page {url} after {settings.SELENIUM_PAGE_LOAD_TIMEOUT} seconds.")
                 try:
                     with open(filepath, 'w', encoding='utf-8') as f:
                         f.write(f"Failed to crawl URL due to timeout: {url}\n")
                         f.write(f"Timeout limit: {settings.SELENIUM_PAGE_LOAD_TIMEOUT} seconds\n")
                 except OSError as write_err:
                     logging.error(f"Failed to write timeout error to log file {filepath}: {write_err}")
            except WebDriverException as e:
                # Handle specific common exceptions if needed (e.g., InvalidSessionIdException)
                logging.error(f"Selenium error navigating to or processing {url}: {e.msg}", exc_info=False) # Keep log cleaner, msg usually sufficient
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Failed to crawl or retrieve logs for URL: {url}\n")
                        f.write(f"Error Type: {type(e).__name__}\n")
                        f.write(f"Error Message: {e.msg}\n")
                except OSError as write_err:
                    logging.error(f"Failed to write WebDriver error to log file {filepath}: {write_err}")
            except Exception as e:
                logging.error(f"Unexpected error processing {url}: {e}", exc_info=True) # Include traceback for unexpected errors
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Unexpected error processing URL: {url}\n")
                        f.write(f"Error Type: {type(e).__name__}\n")
                        f.write(f"Error: {e}\n")
                except OSError as write_err:
                    logging.error(f"Failed to write unexpected error to log file {filepath}: {write_err}")

    except Exception as e:
        logging.error(f"Failed during WebDriver setup or main loop: {e}", exc_info=True)
    finally:
        if driver:
            logging.info("Closing WebDriver...")
            try:
                 driver.quit()
                 logging.info("WebDriver closed successfully.")
            except Exception as quit_err:
                 logging.error(f"Error closing WebDriver: {quit_err}", exc_info=True)


# --- Main Execution ---
if __name__ == "__main__":
    # Get sitemap URL from user input
    start_sitemap_url = input("Enter the URL of the WordPress sitemap (e.g., https://example.com/sitemap.xml): ").strip()

    # Basic validation of the input URL format
    if not start_sitemap_url:
        print("Error: Sitemap URL cannot be empty.")
    elif not (start_sitemap_url.startswith('http://') or start_sitemap_url.startswith('https://')):
        print("Error: Invalid URL format. Please include http:// or https://")
    else:
        # Start the process
        logging.info(f"Starting sitemap processing for: {start_sitemap_url}")

        # 1. Get all unique page URLs from the sitemap(s)
        all_urls = get_all_page_urls(start_sitemap_url)

        if all_urls:
            logging.info(f"Found {len(all_urls)} unique page URLs in the sitemap(s).")
            # 2. Crawl each URL and log console errors based on settings
            crawl_and_log_errors(list(all_urls)) # Convert set to list for ordered iteration (optional, mainly for progress logging)
            logging.info("Crawling process finished.")
        else:
            logging.warning("No page URLs were extracted from the provided sitemap. Check URL and sitemap format, or previous log messages.")

    logging.info("Script finished.")