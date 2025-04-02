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
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities # Deprecated approach
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

# --- Configuration ---
OUTPUT_DIR = "console_errors"
# Optional: Add a delay between page crawls (in seconds) to be polite to servers
CRAWL_DELAY = 1
# Log level for script feedback (INFO, WARNING, ERROR)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# --- End Configuration ---

# Namespace dictionary for parsing sitemaps (common namespaces)
SITEMAP_NS = {
    's': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    # Add other potential namespaces if needed, e.g., 'image', 'video'
}

def sanitize_filename(url):
    """Creates a safe filename from a URL."""
    if not url:
        return "invalid_url"
    # Remove scheme
    parsed_url = urlparse(url)
    path = parsed_url.netloc + parsed_url.path
    # Remove trailing slash if it's the only thing in the path
    if path.endswith('/') and len(path) > 1:
        path = path[:-1]
    # Replace invalid filename characters with underscores
    safe_name = re.sub(r'[\\/*?:"<>|]', '_', path)
    # Replace remaining slashes with underscores for flatter structure
    safe_name = safe_name.replace('/', '_')
    # Truncate if too long (OS limits vary, 200 is generally safe)
    max_len = 200
    if len(safe_name) > max_len:
        safe_name = safe_name[:max_len]
    # Ensure filename is not empty after sanitization
    return f"{safe_name}.log" if safe_name else "index.log"

def get_all_page_urls(sitemap_url, visited_sitemaps=None):
    """
    Recursively fetches and parses sitemaps (index or regular)
    and returns a set of all unique page URLs found.
    """
    if visited_sitemaps is None:
        visited_sitemaps = set()

    if sitemap_url in visited_sitemaps:
        logging.warning(f"Sitemap already visited, skipping: {sitemap_url}")
        return set()

    visited_sitemaps.add(sitemap_url)
    page_urls = set()
    # Identify crawler clearly in User-Agent
    headers = {'User-Agent': 'BoostifyUSA-SitemapCrawler/1.0 (+http://yourwebsite.com/botinfo)'} # Modify with your info URL if available

    try:
        logging.info(f"Fetching sitemap: {sitemap_url}")
        response = requests.get(sitemap_url, headers=headers, timeout=30)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # It's important to use response.content for lxml parsing
        content = response.content
        if not content:
            logging.warning(f"Sitemap is empty: {sitemap_url}")
            return set()

        # Use lxml to parse the XML content
        # Use recover=True to handle potentially malformed XML more gracefully
        parser = etree.XMLParser(recover=True, remove_blank_text=True)
        root = etree.fromstring(content, parser=parser)

        # Check if it's a sitemap index file (handle potential namespace variations)
        if root.tag.endswith('sitemapindex'):
            logging.info(f"Detected sitemap index: {sitemap_url}")
            # Adjusted XPath to be less namespace-strict if needed, but explicit is better
            sitemaps = root.xpath('.//s:sitemap/s:loc/text() | .//sitemap/loc/text()', namespaces=SITEMAP_NS)
            for sub_sitemap_url in sitemaps:
                # Ensure the sub-sitemap URL is absolute
                absolute_sub_url = urljoin(sitemap_url, sub_sitemap_url.strip())
                # Recursively fetch URLs from sub-sitemaps
                page_urls.update(get_all_page_urls(absolute_sub_url, visited_sitemaps))

        # Check if it's a URL set file (handle potential namespace variations)
        elif root.tag.endswith('urlset'):
            logging.info(f"Detected URL set: {sitemap_url}")
            # Adjusted XPath to be less namespace-strict if needed
            urls = root.xpath('.//s:url/s:loc/text() | .//url/loc/text()', namespaces=SITEMAP_NS)
            for page_url in urls:
                 # Basic validation: Ensure it looks like a URL before adding
                 if page_url.strip().startswith('http://') or page_url.strip().startswith('https://'):
                     page_urls.add(page_url.strip())
                 else:
                     logging.warning(f"Skipping invalid/relative URL found in {sitemap_url}: {page_url.strip()}")
        else:
            logging.warning(f"Unknown sitemap format/root tag '{root.tag}' in: {sitemap_url}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch sitemap {sitemap_url}: {e}")
    except etree.XMLSyntaxError as e:
        logging.error(f"Failed to parse XML sitemap {sitemap_url}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {sitemap_url}: {e}")

    return page_urls

def crawl_and_log_errors(urls_to_crawl):
    """
    Crawls each URL using Selenium, captures console errors,
    and saves them to individual files.
    """
    if not urls_to_crawl:
        logging.info("No URLs found to crawl.")
        return

    logging.info(f"Setting up Selenium WebDriver...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu") # Often needed for headless mode
    options.add_argument("--no-sandbox") # Bypass OS security model, required on Linux sometimes
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    options.add_argument("--window-size=1920,1080") # Set a reasonable window size
    options.add_argument("--log-level=3") # Reduce console noise from Chrome/Driver itself
    options.add_experimental_option('excludeSwitches', ['enable-logging']) # Suppress DevTools listening message
    # Set a custom user agent for the browser itself
    options.add_argument(f"user-agent=BoostifyUSA-SitemapCrawler/1.0 Selenium (+http://yourwebsite.com/botinfo)") # Modify with your info URL

    # Enable browser logging to capture console errors
    options.set_capability("goog:loggingPrefs", {"browser": "SEVERE"}) # Capture SEVERE level logs (errors)

    driver = None # Initialize driver to None for finally block
    try:
        # Use webdriver-manager to automatically handle driver download/updates
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        # Set page load timeout and script timeout
        driver.set_page_load_timeout(60) # seconds
        driver.set_script_timeout(30) # seconds

        logging.info("WebDriver setup complete.")

        # Create the output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logging.info(f"Saving error logs to directory: '{OUTPUT_DIR}'")

        total_urls = len(urls_to_crawl)
        logging.info(f"Starting crawl of {total_urls} URLs...")

        for i, url in enumerate(urls_to_crawl, 1):
            logging.info(f"Crawling URL {i}/{total_urls}: {url}")
            error_log_entries = []
            filename = sanitize_filename(url)
            filepath = os.path.join(OUTPUT_DIR, filename)

            try:
                driver.get(url)
                # Wait a bit for dynamic content/scripts to potentially execute and log errors
                # A fixed sleep is simple but not always reliable. Consider Selenium explicit waits if needed.
                time.sleep(CRAWL_DELAY) # Use configured delay

                # Retrieve browser logs
                logs = driver.get_log('browser')

                # Filter for SEVERE errors (typically JS errors)
                for entry in logs:
                    # Example: Filter out less actionable SEVERE messages if needed
                    # msg = entry.get('message', '').lower()
                    # if 'favicon.ico' in msg and '404' in msg: # Ignore missing favicon errors
                    #    continue
                    if entry.get('level') == 'SEVERE':
                         # Format the message for better readability
                        timestamp_ms = entry.get('timestamp', time.time() * 1000)
                        timestamp_sec = timestamp_ms / 1000.0
                        log_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_sec))
                        message = entry.get('message', 'No message content.')
                        # Clean up potential WebDriver noise in message
                        message = message.replace('\\n', '\n').replace('\\u003C', '<')
                        error_log_entries.append(f"[{log_time}] {entry['level']} - {message}")


                # Save errors to the specific file for this URL
                with open(filepath, 'w', encoding='utf-8') as f:
                    if error_log_entries:
                        logging.warning(f"Found {len(error_log_entries)} SEVERE error(s) on: {url}")
                        f.write(f"Console errors found on: {url}\n")
                        f.write("=" * 30 + "\n")
                        for error in error_log_entries:
                            f.write(error + "\n\n") # Add extra newline for readability
                    else:
                        # logging.info(f"No console errors found on: {url}") # Can be noisy
                        f.write(f"No SEVERE console errors found on: {url}\n")
                # print(f"Log saved for {url} -> {filepath}") # Optional: print progress for each file

            except WebDriverException as e:
                # Catch specific timeout errors differently if desired
                # from selenium.common.exceptions import TimeoutException
                # if isinstance(e, TimeoutException):
                #    logging.error(f"Timeout loading page {url}: {e.msg}")
                # else:
                logging.error(f"Selenium error navigating to or processing {url}: {e.msg}")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Failed to crawl or retrieve logs for URL: {url}\n")
                    f.write(f"Error Type: {type(e).__name__}\n")
                    f.write(f"Error Message: {e.msg}\n") # Use e.msg for better Selenium error details
            except Exception as e:
                logging.error(f"Unexpected error processing {url}: {e}")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Unexpected error processing URL: {url}\n")
                    f.write(f"Error Type: {type(e).__name__}\n")
                    f.write(f"Error: {e}\n")

    except Exception as e:
        logging.error(f"Failed to initialize Selenium WebDriver: {e}")
    finally:
        if driver:
            logging.info("Closing WebDriver...")
            driver.quit()
            logging.info("WebDriver closed.")

# --- Main Execution ---
if __name__ == "__main__":
    # Get sitemap URL from user
    start_sitemap_url = input("Enter the URL of the WordPress sitemap (e.g., https://example.com/sitemap.xml): ").strip()

    if not start_sitemap_url:
        print("Error: Sitemap URL cannot be empty.")
    elif not (start_sitemap_url.startswith('http://') or start_sitemap_url.startswith('https://')):
        print("Error: Invalid URL format. Please include http:// or https://")
    else:
        # 1. Get all unique page URLs from the sitemap(s)
        all_urls = get_all_page_urls(start_sitemap_url)

        if all_urls:
            logging.info(f"Found {len(all_urls)} unique page URLs in the sitemap(s).")
            # 2. Crawl each URL and log console errors
            crawl_and_log_errors(list(all_urls)) # Convert set to list for ordered iteration (optional)
            logging.info("Crawling process finished.")
        else:
            logging.warning("No page URLs were extracted from the provided sitemap. Check URL and sitemap format.")