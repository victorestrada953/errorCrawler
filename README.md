# Sitemap Console Error Crawler

**Author:** Boostify USA
**Date:** 07/22/2024 (Script Creation)
**License:** MIT License

## Overview

This Python script crawls URLs found within a given WordPress sitemap (including sitemap index files). It uses Selenium and a headless Chrome browser to load each page, execute JavaScript, and capture console errors **at a configurable level**. The errors for each crawled page are saved into a separate log file.

**Configuration is now managed via the `settings.py` file.**

## Features

* Accepts a starting sitemap URL (e.g., `sitemap.xml` or `sitemap_index.xml`).
* Recursively processes sitemap index files to find all page URLs.
* Uses Selenium with headless Chrome to accurately render pages and run JavaScript.
* Captures **configurable level** console logs (default: `SEVERE`, typically JavaScript errors) for each page.
* Saves relevant console logs for **each URL** into its own file within a dedicated output directory.
* Optionally skips creating log files for pages with no relevant errors found.
* Handles potential errors during fetching or crawling gracefully.
* Uses `webdriver-manager` to automatically download and manage the appropriate ChromeDriver.
* **Highly configurable** via `settings.py` file (headless mode, timeouts, log levels, output, filters, etc.).

## Requirements

* **Python 3.x** installed.
* **Google Chrome** browser installed on your system.
* Required Python packages listed in `requirements.txt`.

## Setup

1.  Ensure you have Python 3 and Google Chrome installed.
2.  Clone or download the script files (`sitemap_crawler.py`, `settings.py`, `requirements.txt`, `README.md`).
3.  Navigate to the script's directory in your terminal.
4.  Install the necessary Python libraries:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Review and modify `settings.py`** to adjust configuration parameters as needed before running.

## Usage

1.  Open your terminal and navigate to the script's directory.
2.  Run the script using Python:
    ```bash
    python sitemap_crawler.py
    ```
3.  The script will prompt you to enter the full URL of the sitemap you want to crawl. Paste the URL and press Enter.
    ```
    Enter the URL of the WordPress sitemap (e.g., [https://example.com/sitemap.xml](https://example.com/sitemap.xml)): YOUR_SITEMAP_URL_HERE
    ```
4.  The script will then fetch the sitemap(s), initialize the browser based on `settings.py`, and begin crawling the found URLs. Progress and status messages will be logged to the console according to the configured script log level.

## Output

* Console logs for each crawled page are stored in the directory specified by `OUTPUT_DIRECTORY` in `settings.py` (default: `console_errors`). This folder is created automatically if it doesn't exist.
* Each file within the output directory corresponds to one crawled URL and contains any console logs found **at or above the level specified by `BROWSER_LOG_LEVEL` in `settings.py`** (default: `SEVERE`), excluding messages filtered by `FILTER_LOG_MESSAGES`.
* If `CREATE_EMPTY_LOG_FILES` is set to `False` in `settings.py`, files will **only** be created for pages where relevant logs were captured. Otherwise (if `True`), a file indicating "No relevant console errors found" will be created for pages without captured logs.
* Filenames are generated based on the URL structure (e.g., `example_com_page_subpage.log`).

**---> IMPORTANT NOTE ON OUTPUT FOLDER <---**

* The script **will add logs to the existing output directory** specified in `settings.py` every time it is run.
* If you want to keep the results of different crawls separate, you **MUST rename or move the output directory** after a run finishes and before starting a new one (or change `OUTPUT_DIRECTORY` in `settings.py`). Otherwise, logs from subsequent runs will be mixed in with the previous ones, or files might be overwritten if URLs are the same.

## Configuration

All script configuration is now handled by editing the **`settings.py`** file. You can modify various parameters without changing the main `sitemap_crawler.py` script. Key options include:

**General:**
* `OUTPUT_DIRECTORY`: Folder name for saving log files (default: `"console_errors"`).
* `CRAWL_DELAY`: Delay in seconds between page crawls (default: `1`).
* `CREATE_EMPTY_LOG_FILES`: Set to `False` to prevent creating log files for pages with no captured errors (default: `True`).

**Logging:**
* `SCRIPT_LOG_LEVEL`: Verbosity of the script's own console output (e.g., `logging.INFO`, `logging.DEBUG`).
* `BROWSER_LOG_LEVEL`: The minimum log level to capture from the browser console (e.g., `'SEVERE'`, `'WARNING'`, `'INFO'`). Capturing lower levels can create large logs.
* `FILTER_LOG_MESSAGES`: A list of strings; log messages containing any of these substrings (case-insensitive) will be ignored (default: `[]`).

**Selenium/Browser:**
* `SELENIUM_HEADLESS`: Run Chrome without a visible window (`True`/`False`).
* `SELENIUM_DISABLE_GPU`, `SELENIUM_NO_SANDBOX`, `SELENIUM_DISABLE_DEV_SHM_USAGE`: Flags for compatibility/headless operation.
* `SELENIUM_USER_AGENT`: Custom User-Agent string for the browser.
* `SELENIUM_WINDOW_SIZE`: Browser window dimensions (e.g., `"1920,1080"`).
* `SELENIUM_PAGE_LOAD_TIMEOUT`: Max time (seconds) to wait for page loads.
* `SELENIUM_SCRIPT_TIMEOUT`: Max time (seconds) for asynchronous scripts to execute.

**Requests (Sitemap Fetching):**
* `REQUESTS_USER_AGENT`: User-Agent for fetching sitemap files.
* `REQUESTS_TIMEOUT`: Timeout (seconds) for fetching sitemaps.

*Please refer to the comments within `settings.py` for details on all available options.*

## Notes & Nuances

* The script relies on `webdriver-manager` to automatically download the correct ChromeDriver version for your installed Google Chrome. An internet connection is required the first time it runs (or when Chrome updates) for this download.
* Crawl time can vary significantly depending on the number of URLs in the sitemap, the complexity of the pages, server response times, and the configured `CRAWL_DELAY`.
* The types and amount of logs captured depend heavily on the `BROWSER_LOG_LEVEL` setting, website behavior, and browser updates.
* The script includes a basic politeness delay (`CRAWL_DELAY`). Be mindful of the target website's `robots.txt` and terms of service. Avoid running excessively frequent or aggressive crawls.
* Websites with strong anti-bot measures might block the crawler or present CAPTCHAs, which this script is not designed to handle.
* Page load and script timeouts **can be configured in `settings.py`** and might need adjustment for very slow-loading sites or complex JavaScript applications.

## License

This project is licensed under the MIT License - see the header comment in `sitemap_crawler.py` for details.