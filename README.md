# Sitemap Console Error Crawler

**Author:** Boostify USA
**Date:** 07/22/2024 (Script Creation)
**License:** MIT License

## Overview

This Python script crawls URLs found within a given WordPress sitemap (including sitemap index files). It uses Selenium and a headless Chrome browser to load each page, execute JavaScript, and capture any severe-level console errors. The errors for each crawled page are saved into a separate log file.

## Features

* Accepts a starting sitemap URL (e.g., `sitemap.xml` or `sitemap_index.xml`).
* Recursively processes sitemap index files to find all page URLs.
* Uses Selenium with headless Chrome to accurately render pages and run JavaScript.
* Captures `SEVERE` level console logs (typically JavaScript errors) for each page.
* Saves console logs for **each URL** into its own file within a dedicated output directory.
* Handles potential errors during fetching or crawling gracefully.
* Uses `webdriver-manager` to automatically download and manage the appropriate ChromeDriver.

## Requirements

* **Python 3.x** installed.
* **Google Chrome** browser installed on your system.
* Required Python packages listed in `requirements.txt`.

## Setup

1.  Ensure you have Python 3 and Google Chrome installed.
2.  Clone or download the script files (`sitemap_crawler.py`, `requirements.txt`, `README.md`).
3.  Navigate to the script's directory in your terminal.
4.  Install the necessary Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

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
4.  The script will then fetch the sitemap(s), initialize the browser, and begin crawling the found URLs. Progress and status messages will be logged to the console.

## Output

* Console error logs for each crawled page are stored in a directory named `console_errors` (this folder is created automatically if it doesn't exist).
* Each file within `console_errors` corresponds to one crawled URL and contains any `SEVERE` console errors found, or a message indicating that no severe errors were detected.
* Filenames are generated based on the URL structure (e.g., `example_com_page_subpage.log`).

**---> IMPORTANT NOTE ON OUTPUT FOLDER <---**

* The script **will add logs to the existing `console_errors` folder** every time it is run.
* If you want to keep the results of different crawls separate, you **MUST rename or move the `console_errors` folder** after a run finishes and before starting a new one. Otherwise, logs from subsequent runs will be mixed in with the previous ones, or files might be overwritten if URLs are the same.

## Configuration (Optional)

You can modify the following variables directly within the `sitemap_crawler.py` script if needed:

* `OUTPUT_DIR`: Change the name of the directory where logs are saved (default: `"console_errors"`).
* `CRAWL_DELAY`: Adjust the delay (in seconds) between crawling each page (default: `1`). Increasing this can be important for respecting server resources on the target website.

## Notes & Nuances

* The script relies on `webdriver-manager` to automatically download the correct ChromeDriver version for your installed Google Chrome. An internet connection is required the first time it runs (or when Chrome updates) for this download.
* Crawl time can vary significantly depending on the number of URLs in the sitemap, the complexity of the pages, server response times, and the configured `CRAWL_DELAY`.
* While the script captures `SEVERE` errors, website behavior and browser updates might affect what gets logged.
* The script includes a basic politeness delay (`CRAWL_DELAY`). Be mindful of the target website's `robots.txt` and terms of service. Avoid running excessively frequent or aggressive crawls.
* Websites with strong anti-bot measures might block the crawler or present CAPTCHAs, which this script is not designed to handle.
* Page load timeouts are set within the script but might need adjustment for very slow-loading sites.

## License

This project is licensed under the MIT License - see the header comment in `sitemap_crawler.py` for details.