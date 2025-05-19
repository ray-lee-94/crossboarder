import os
import csv # Keep for potential logging or other uses, but not primary output for API
import time
import logging
import threading
import traceback
import re
import random
import platform
from urllib.parse import urlparse, quote_plus, urljoin
from typing import List, Dict, Tuple, Union, Optional, Any


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    StaleElementReferenceException, NoSuchElementException, TimeoutException
)
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import uuid # For generating job IDs

# Determine the base directory of this Python script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- LogWeek Class (Keep As Is or use standard logging) ---
class LogWeek:
    def get_logger(self):
        logger = logging.getLogger("AmazonCrawlerAPI") # Give it a distinct name
        if logger.hasHandlers():
            # logger.handlers.clear() # Be careful if other parts of app use root logger
            pass # Avoid clearing if other parts of a larger app might configure logging
        if not logger.handlers: # Only add handlers if none exist for this logger
            formatter = '[%(asctime)s-%(filename)s][%(funcName)s-%(lineno)d]--%(message)s'
            logger.setLevel(logging.DEBUG)
            sh = logging.StreamHandler()
            log_formatter = logging.Formatter(formatter, datefmt='%Y-%m-%d %H:%M:%S')
            sh.setFormatter(log_formatter)
            logger.addHandler(sh)
            logs_dir = os.path.join(BASE_DIR, "logs_api") # Separate logs for API
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            info_file_name = time.strftime("%Y-%m-%d") + '_api.log'
            info_handler = TimedRotatingFileHandler(
                filename=os.path.join(logs_dir, info_file_name),
                when='MIDNIGHT', interval=1, backupCount=7, encoding='utf-8'
            )
            info_handler.setFormatter(log_formatter)
            logger.addHandler(info_handler)
        return logger

# Global logger instance for the crawler
crawler_logger = LogWeek().get_logger()

class AmazonCrawler:
    PAGE_LOAD_TIMEOUT = 30
    ELEMENT_WAIT_TIMEOUT = 20
    PRODUCT_DETAIL_TIMEOUT = 25 # Increased slightly

    def __init__(self, logger_instance=None): # Removed ui_callback and target_count
        self.logger = logger_instance if logger_instance else crawler_logger
        self.browser = None # Initialize browser later

    def _init_browser(self):
        if self.browser:
            try:
                self.browser.current_url
                return
            except Exception:
                self.logger.info("Browser seems to be closed or unresponsive, re-initializing.")
                try:
                    self.browser.quit()
                except:
                    pass
                self.browser = None

        self.logger.info("Initializing browser...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox") # Often necessary in Linux Docker/server environments
        chrome_options.add_argument("--lang=en-US,en;q=0.9")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--disable-dev-shm-usage') # Crucial for Docker/CI
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        executable_path = None # Will store the path if found manually

        # --- Attempt to find a suitable local ChromeDriver ---
        os_platform = platform.system().lower()
        self.logger.info(f"Operating System: {os_platform}")

        if os_platform == "linux":
            linux_driver_names = ["chromedriver", "chromedriver_linux64"] 
            possible_linux_paths = [ # Order these by preference
                Path(BASE_DIR) / "chromedriver_linux64" / "chromedriver",
                Path(BASE_DIR) / "chromedriver",
                Path("/usr/local/bin/chromedriver"),
                Path("/usr/bin/chromedriver"),
            ]
            # Check project-relative paths first by combining names and BASE_DIR
            for name in linux_driver_names:
                p_rel_dir = Path(BASE_DIR) / name # Case where name is a directory like 'chromedriver_linux64'
                p_rel_file_in_dir = p_rel_dir / "chromedriver" # Actual driver inside that dir
                p_rel_direct = Path(BASE_DIR) / name # Case where name is the driver file itself like 'chromedriver'

                paths_to_check_local = []
                if p_rel_dir.is_dir(): # Check if 'name' is a directory containing 'chromedriver'
                    paths_to_check_local.append(p_rel_file_in_dir)
                paths_to_check_local.append(p_rel_direct)


                for p in paths_to_check_local:
                    if p.exists() and p.is_file() and os.access(p, os.X_OK):
                        executable_path = str(p)
                        self.logger.info(f"Found executable Linux ChromeDriver at: {executable_path}")
                        break
                if executable_path:
                    break
            
            if not executable_path: # If not found in project relative, check system paths
                for p_abs in possible_linux_paths: # These are already full paths
                    if p_abs.exists() and p_abs.is_file() and os.access(p_abs, os.X_OK):
                        executable_path = str(p_abs)
                        self.logger.info(f"Found executable Linux ChromeDriver at: {executable_path}")
                        break
        elif os_platform == "windows":
            windows_driver_paths = [
                Path(BASE_DIR) / "chromedriver-win64" / "chromedriver.exe",
                Path(BASE_DIR) / "chromedriver-win64" / "chromedriver-win64" / "chromedriver.exe"
            ]
            for p in windows_driver_paths:
                if p.exists() and p.is_file():
                    executable_path = str(p)
                    self.logger.info(f"Found Windows ChromeDriver at: {executable_path}")
                    break
        elif os_platform == "darwin": # macOS
            macos_driver_names = ["chromedriver", "chromedriver_mac64", "chromedriver_mac_arm64"]
            # Simplified: Check project relative first, then system paths like for Linux
            for name in macos_driver_names:
                p_rel = Path(BASE_DIR) / name
                if p_rel.exists() and p_rel.is_file() and os.access(p_rel, os.X_OK):
                    executable_path = str(p_rel)
                    break
                # Also check if 'name' is a directory containing 'chromedriver'
                p_rel_dir = Path(BASE_DIR) / name / "chromedriver"
                if p_rel_dir.exists() and p_rel_dir.is_file() and os.access(p_rel_dir, os.X_OK):
                    executable_path = str(p_rel_dir)
                    break
            if executable_path:
                 self.logger.info(f"Found executable macOS ChromeDriver at: {executable_path}")

            if not executable_path: # Check common system paths for macOS
                system_macos_paths = [Path("/usr/local/bin/chromedriver")]
                for p_sys in system_macos_paths:
                    if p_sys.exists() and p_sys.is_file() and os.access(p_sys, os.X_OK):
                        executable_path = str(p_sys)
                        self.logger.info(f"Found executable macOS ChromeDriver at: {executable_path}")
                        break
        
        try:
            if executable_path:
                self.logger.info(f"Attempting to use local ChromeDriver: {executable_path}")
                service = Service(executable_path=executable_path)
                self.browser = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.logger.info("No suitable local ChromeDriver found or specified. "
                                 "Attempting automatic download by Selenium Manager...")
                self.browser = webdriver.Chrome(options=chrome_options)
                self.logger.info("Using automatically managed ChromeDriver.")

            self.browser.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
            self.logger.info("Browser initialized successfully.")
        except Exception as e:
            self.logger.error(f"Browser initialization failed: {e}")
            self.logger.error(traceback.format_exc())
            if "executable needs to be in PATH" in str(e) or "unable to locate" in str(e).lower():
                self.logger.error("Ensure Chrome/Chromium browser is installed and that "
                                  "the correct ChromeDriver is either in your system PATH, "
                                  "specified correctly, or can be managed by Selenium Manager.")
            if self.browser:
                try:
                    self.browser.quit()
                except: pass
            self.browser = None 
            raise

    def log(self, message, level="info"): # Modified log method
        if level == "info":
            self.logger.info(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.debug(message)

    def _extract_product_details(self, product_url, platform="Amazon"): # Added platform, category_name is now 'source_hint'
        """Extract detailed product information (largely same as original)"""
        details = {'platform': platform, 'product_url': product_url} # Store platform and original URL

        try:
            self.browser.get(product_url)
            WebDriverWait(self.browser, self.PRODUCT_DETAIL_TIMEOUT).until(
                EC.any_of(
                   EC.presence_of_element_located((By.ID, "productTitle")),
                   EC.presence_of_element_located((By.ID, "landingImage"))
                )
            )
        except TimeoutException:
            self.log(f"Timeout loading product page: {product_url}", "error")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = os.path.join(BASE_DIR, "logs_api", f"timeout_{timestamp}_{details.get('asin', 'NO_ASIN')}.png")
        try:
            self.browser.save_screenshot(screenshot_path)
            self.log(f"Screenshot saved to {screenshot_path} on timeout.")
        except Exception as ss_err:
            self.log(f"Failed to save screenshot: {ss_err}", "error")
            return None

        # --- Extraction logic (mostly unchanged, copy from your original, ensure self.log is used) ---
        # Product Title
        try:
            product_title_elem = self.browser.find_element(By.ID, "productTitle")
            details['product_title'] = product_title_elem.text.strip()
        except NoSuchElementException:
            details['product_title'] = "N/A"
            self.log(f"Product title not found for {product_url}", "warning")

        # ASIN
        details['asin'] = "N/A"
        try:
             asin_match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', product_url)
             if asin_match:
                 details['asin'] = asin_match.group(2)
             else: # Fallback
                 td_elements = self.browser.find_elements(By.CSS_SELECTOR, "th.prodDetSectionEntry")
                 for th in td_elements:
                     if "ASIN" in th.text:
                         asin_td = th.find_element(By.XPATH, "./following-sibling::td")
                         details['asin'] = asin_td.text.strip() if asin_td else "N/A"
                         break
                 if details['asin'] == "N/A":
                     page_source = self.browser.page_source
                     asin_match_src = re.search(r'ASIN\s*[:=]\s*"([A-Z0-9]{10})"', page_source) or \
                                      re.search(r'"ASIN"\s*:\s*"([A-Z0-9]{10})"', page_source)
                     if asin_match_src: details['asin'] = asin_match_src.group(1)
        except Exception as e:
            self.log(f"ASIN extraction error for {product_url}: {e}", "warning")

        # Price
        details['price'] = "N/A"
        price_selectors = [
            "span.a-price span[aria-hidden='true']", "span.a-price span.a-offscreen",
            "#priceblock_ourprice", "#priceblock_dealprice", ".priceToPay span.a-price-whole",
            ".apexPriceToPay span[aria-hidden='true']"
        ]
        for selector in price_selectors:
            try:
                price_elems = self.browser.find_elements(By.CSS_SELECTOR, selector)
                visible_prices = [p.text.strip() for p in price_elems if p.is_displayed() and p.text.strip()]
                if visible_prices:
                    details['price'] = visible_prices[0]
                    if selector == ".priceToPay span.a-price-whole":
                         try:
                             fraction = self.browser.find_element(By.CSS_SELECTOR,".priceToPay span.a-price-fraction").text.strip()
                             details['price'] += f".{fraction}"
                         except NoSuchElementException: pass
                    break
            except (NoSuchElementException, StaleElementReferenceException): continue
        if details['price'] == "N/A": self.log(f"Price not found for {product_url}", "warning")

        # Rating
        details['rating'] = "N/A"
        try:
            rating_elem = self.browser.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
            rating_text = rating_elem.get_attribute("innerHTML")
            rating_match = re.search(r'(\d+\.\d+|\d+)', rating_text)
            details['rating'] = rating_match.group(1) if rating_match else "N/A"
        except (NoSuchElementException, StaleElementReferenceException): pass

        # Review Count
        details['review_count'] = "0"
        try:
            review_count_elem = self.browser.find_element(By.ID, "acrCustomerReviewText")
            review_text = review_count_elem.text.strip()
            review_match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)', review_text)
            if review_match:
                details['review_count'] = review_match.group(1).replace(',', '')
        except (NoSuchElementException, StaleElementReferenceException): pass
        
        # Monthly Sales
        details["monthly_sales"]= "N/A"
        try:
            sales_text_elem = self.browser.find_element(By.ID, "social-proofing-faceout-title-tk_bought")
            sales_text = sales_text_elem.text.strip()
            sales_match = re.search(r'(\d{1,3}(?:,\d{3})*k\+|\d{1,3}(?:,\d{3})*|\d+)', sales_text) # Handles 1k+, 100+, etc.
            if sales_match:
                details['monthly_sales'] = sales_match.group(1).replace(',', '').replace('k+', '000+') #粗略转换
        except (NoSuchElementException, StaleElementReferenceException): pass

        # Availability
        details['availability'] = "N/A"
        try:
            availability_elem = self.browser.find_element(By.CSS_SELECTOR, "#availability span")
            details['availability'] = availability_elem.text.strip()
            if not details['availability']:
                 availability_elem = self.browser.find_element(By.ID, "availability")
                 details['availability'] = availability_elem.text.strip()
        except (NoSuchElementException, StaleElementReferenceException): pass

        # Seller & Seller URL
        details['seller'] = "Amazon" # Default
        details['seller_url'] = "N/A"
        seller_selectors = [
            "#sellerProfileTriggerId",
            "#merchant-info a",
            "#tabular-buybox-container .tabular-buybox-text[tabular-attribute-name='Sold by'] a",
            "#bylineInfo"
        ]
        seller_href_for_address = None
        for selector in seller_selectors:
            try:
                seller_elem = self.browser.find_element(By.CSS_SELECTOR, selector)
                seller_text = seller_elem.text.strip()
                seller_href = seller_elem.get_attribute("href")
                if seller_text and "Visit" not in seller_text and "Store" not in seller_text:
                    details['seller'] = seller_text
                    details['seller_url'] = seller_href if seller_href and seller_href.startswith('http') else "N/A"
                    if details['seller_url'] != "N/A":
                        seller_href_for_address = details['seller_url']
                    break
            except (NoSuchElementException, StaleElementReferenceException): continue
        
        # Image URL
        details['image_url'] = "N/A"
        img_selectors = ["#landingImage", "#imgBlkFront", "#main-image-container img"]
        for selector in img_selectors:
            try:
                img_elem = self.browser.find_element(By.CSS_SELECTOR, selector)
                img_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src")
                if img_url and not img_url.startswith("data:image"):
                    details['image_url'] = img_url
                    break
            except (NoSuchElementException, StaleElementReferenceException): continue

        # Features
        details['features'] = "N/A"
        try:
            bullet_parents = ["#feature-bullets", "#productOverview_feature_div"]
            feature_list = []
            for parent_selector in bullet_parents:
                try:
                    parent_elem = self.browser.find_element(By.CSS_SELECTOR, parent_selector)
                    try:
                        see_more_link = parent_elem.find_element(By.CSS_SELECTOR, "a[data-action='a-expander-toggle']")
                        if see_more_link.is_displayed():
                            self.browser.execute_script("arguments[0].click();", see_more_link)
                            time.sleep(0.5)
                    except NoSuchElementException: pass
                    feature_bullets = parent_elem.find_elements(By.CSS_SELECTOR, "li span.a-list-item")
                    features_text = [bullet.text.strip() for bullet in feature_bullets if bullet.text.strip()]
                    if features_text: feature_list.extend(features_text)
                except (NoSuchElementException, StaleElementReferenceException): continue
            if feature_list: details['features'] = " | ".join(feature_list)
        except Exception as e: self.log(f"Feature extraction error: {e}", "warning")

        # Description
        details['description'] = "N/A"
        desc_selectors = ["#productDescription", "#aplus_feature_div", "#aplus", "#dpx-product-description_feature_div"]
        desc_text_parts = []
        for selector in desc_selectors:
            try:
                desc_elems = self.browser.find_elements(By.CSS_SELECTOR, selector)
                for desc_elem in desc_elems:
                     if desc_elem.is_displayed(): desc_text_parts.append(desc_elem.text.strip())
            except (NoSuchElementException, StaleElementReferenceException): continue
        if desc_text_parts: details['description'] = " ".join(desc_text_parts).strip()[:2000] # Limit length

        # Brand Name
        details['brand_name'] = "N/A"
        try:
            brand_element = self.browser.find_element(By.CSS_SELECTOR, "tr.po-brand > td.a-span9 > span.po-break-word")
            details['brand_name'] = brand_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            try: # Fallback byline
                brand_byline = self.browser.find_element(By.ID, "bylineInfo")
                if "Visit the" in brand_byline.text or "Brand:" in brand_byline.text :
                    details['brand_name'] = brand_byline.text.replace("Visit the","").replace("Brand:","").strip().split(" Store")[0] # Heuristic
            except NoSuchElementException:
                self.log(f"Brand name not found for {product_url}", "warning")

        # Listing Date (上架时间)
        details['listing_date'] = "N/A"
        date_labels = ["Date First Available", "上架时间"] # English and Chinese
        for label in date_labels:
            try:
                # More robust XPath, looking for th containing the label text, then its sibling td
                date_th = self.browser.find_element(By.XPATH, f"//th[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='{label.lower()}']")
                date_td = date_th.find_element(By.XPATH, "./following-sibling::td")
                details['listing_date'] = date_td.text.strip()
                if details['listing_date'] != "N/A": break
            except NoSuchElementException: continue
        
        # BSR Rank
        details["bsr_rank_full_text"] = "N/A" # Store full BSR text
        details["bsr_top_category_rank"] = "N/A" # Store just the first rank number
        try:
            # This often varies significantly. Try a few common patterns.
            bsr_selectors = [
                "//*[contains(text(),'Best Sellers Rank') or contains(text(),'Best Sellers Rank')]/following-sibling::td/span", # Table format
                "//*[contains(text(),'Best Sellers Rank') or contains(text(),'Best Sellers Rank')]/parent::li", # List format
                "//div[@id='detailBullets_feature_div']//li[contains(., 'Best Sellers Rank')]", # Another common location
                "//ul[contains(@class, 'detail-bullet-list')]//li[contains(., 'Best Sellers Rank')]"
            ]
            found_bsr_text = None
            for selector in bsr_selectors:
                try:
                    bsr_elements = self.browser.find_elements(By.XPATH, selector)
                    for bsr_elem in bsr_elements:
                        text_content = bsr_elem.text.strip()
                        if "Best Sellers Rank" in text_content or "亚马逊热销商品排名" in text_content : # Amazon.cn
                            found_bsr_text = text_content
                            break
                    if found_bsr_text: break
                except NoSuchElementException: continue
            
            if found_bsr_text:
                details["bsr_rank_full_text"] = found_bsr_text
                # Try to extract the primary rank number
                rank_match = re.search(r'#([\d,]+)\s+in', found_bsr_text) # e.g., #1,234 in Books
                if not rank_match: # Chinese version
                    rank_match = re.search(r'商品里排第(\d+)名', found_bsr_text)
                if rank_match:
                    details["bsr_top_category_rank"] = rank_match.group(1).replace(',', '')
        except Exception as e:
            self.log(f"BSR extraction error: {e}", "warning")

        # Seller Address (if seller_url was found and is an Amazon seller profile link)
        details['seller_address'] = "N/A"
        if seller_href_for_address and "amazon.com/sp?" in seller_href_for_address: # Check if it's a seller profile page
            try:
                self.log(f"Fetching seller address from: {seller_href_for_address}")
                # It's good practice to GET a new page in a new tab or be careful with navigation
                # For simplicity, we'll navigate directly. Consider impact on subsequent extractions if this fails.
                current_product_page_url = self.browser.current_url
                self.browser.get(seller_href_for_address)
                WebDriverWait(self.browser, self.PRODUCT_DETAIL_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "page-section-detail-seller-info")) # Wait for seller info section
                )
                address_lines = []
                # Common selectors for address parts on seller profile page
                address_elements = self.browser.find_elements(By.CSS_SELECTOR, 
                    "#page-section-detail-seller-info .a-row .a-spacing-none, #page-section-detail-seller-info span.a-list-item" 
                ) # This selector is a guess, inspect actual seller page
                
                # More specific: Look for "Business Address" or similar label
                try:
                    business_address_header = self.browser.find_element(By.XPATH, "//*[contains(text(), 'Business Address') or contains(text(), '详细卖家信息') or contains(text(),'Geschäftsadresse')]")
                    parent_container = business_address_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'a-box-inner') or contains(@class, 'spp-detail-section-wrapper')][1]") # Find parent box
                    
                    # Extract all text nodes under this parent, attempt to piece together address
                    # This is complex due_to varied HTML, a simpler approach:
                    address_spans = parent_container.find_elements(By.XPATH, ".//span[normalize-space()]") # Get all non-empty spans
                    relevant_texts = []
                    # Filter out known non-address parts like "Business Name:", "VAT number:" etc.
                    ignore_keywords = ["business name", "vat number", "trade register number", "customer service address", "phone", "email", "名称", "增值税", "电话"]
                    
                    current_line = []
                    for span in address_spans:
                        text = span.text.strip()
                        if text and not any(keyword in text.lower() for keyword in ignore_keywords):
                            current_line.append(text)
                        elif current_line: # If we hit a non-address keyword or empty text, and current_line has something
                            relevant_texts.append(" ".join(current_line))
                            current_line = []
                    if current_line: # Append last line
                        relevant_texts.append(" ".join(current_line))

                    # Heuristic: the longest string is likely the address, or a few concatenated lines
                    if relevant_texts:
                        details['seller_address'] = " | ".join(list(dict.fromkeys(relevant_texts))) # Join unique lines

                except NoSuchElementException:
                    self.log(f"Could not find 'Business Address' section on seller page {seller_href_for_address}", "warning")
                
                self.browser.get(current_product_page_url) # Navigate back
                WebDriverWait(self.browser, self.PRODUCT_DETAIL_TIMEOUT).until(EC.presence_of_element_located((By.ID, "productTitle"))) # Wait for product page to reload

            except TimeoutException:
                self.log(f"Timeout loading seller page: {seller_href_for_address}", "warning")
            except Exception as e:
                self.log(f"Error fetching/parsing seller address from {seller_href_for_address}: {e}", "warning")
                # Attempt to navigate back if error occurs
                try:
                    self.browser.get(current_product_page_url)
                    WebDriverWait(self.browser, self.PRODUCT_DETAIL_TIMEOUT).until(EC.presence_of_element_located((By.ID, "productTitle")))
                except Exception as nav_back_e:
                    self.log(f"Failed to navigate back to product page after seller address error: {nav_back_e}", "error")

        return details

    def crawl_one_product(self, product_url: str, platform: str = "Amazon"):
        """Crawls a single product URL and returns its details."""
        self.log(f"Starting crawl for single product: {product_url}")
        try:
            self._init_browser() # Ensure browser is ready
            if not self.browser:
                return {"error": "Browser could not be initialized."}
            
            product_details = self._extract_product_details(product_url, platform=platform)
            
            if product_details:
                self.log(f"Successfully extracted details for: {product_url}")
                return product_details
            else:
                self.log(f"Failed to extract details for: {product_url}", "error")
                return {"error": f"Failed to extract details for {product_url}"}
        except Exception as e:
            self.log(f"Critical error during crawl_one_product for {product_url}: {e}", "error")
            self.log(traceback.format_exc(), "error")
            return {"error": str(e)}
        finally:
            self.quit_browser() # Ensure browser is closed after each single product crawl

    def quit_browser(self):
        if self.browser:
            try:
                self.browser.quit()
                self.log("Browser quit successfully.")
            except Exception as e:
                self.log(f"Error quitting browser: {e}", "error")
            finally:
                self.browser = None



# This `jobs` dictionary should ideally be managed by a more robust system
# (e.g., Redis, a database, or a proper task queue like Celery) for production.
# For this example, it's kept in memory.
jobs: Dict[str, Dict[str, Any]] = {}

def run_crawl_task(job_id: str, product_url: str, platform: str):
    crawler_logger.info(f"Background task started for job ID: {job_id}, URL: {product_url}")
    jobs[job_id]["status"] = "running"
    jobs[job_id]["updated_at"] = time.time()
    
    crawler_instance = None
    try:
        # Instantiate crawler for each task, or use a shared one carefully.
        # For simplicity, creating a new one ensures clean state.
        crawler_instance = AmazonCrawler(logger_instance=crawler_logger)
        product_data = crawler_instance.crawl_one_product(product_url, platform)
        
        if product_data and not product_data.get("error"): # Check for no error key or None/empty error
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = product_data
            crawler_logger.info(f"Job ID: {job_id} completed successfully.")
        else: # Handles cases where product_data is None, empty, or has an "error" field
            error_message = product_data.get("error", "Unknown error: No data returned from crawler.") if product_data else "Unknown error: No data returned from crawler."
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["result"] = product_data if product_data else {"error": error_message, "product_url": product_url, "platform": platform}
            jobs[job_id]["message"] = error_message
            crawler_logger.error(f"Job ID: {job_id} failed: {error_message}")

    except Exception as e:
        crawler_logger.error(f"Unhandled exception in background task for job ID {job_id}: {e}")
        crawler_logger.error(traceback.format_exc())
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Internal server error: {str(e)}"
        jobs[job_id]["result"] = {"error": f"Crawler task failed: {str(e)}", "product_url": product_url, "platform": platform}
    finally:
        if crawler_instance:
             crawler_instance.quit_browser() # Ensure browser is quit
        jobs[job_id]["updated_at"] = time.time()
        crawler_logger.info(f"Background task finished for job ID: {job_id}, Status: {jobs[job_id]['status']}")

if __name__=="__main__":
    crawler=AmazonCrawler()
    print(crawler.crawl_one_product("https://www.amazon.com/-/zh/dp/B000I0DBH6/ref=sr_1_1?dib=eyJ2IjoiMSJ9.p0E_WtU98sBXVepmVF2a_cpsXmF6L27Y_MbcSRn7BL2Dbw1I1lG1MZQeXVV1Ldqbc4X3unFqYSrgFD5XSqoXarZm4G6Ch_f-mZYat-8Lm0Q5cuJ2vb_YcAKmwJrKzlCsxXbUCHndhCME3_wKnw-VXv5YjNJCmBqCsJ4oqoBzc1GFlk-xEz_5rr25NU7zjS83rTtvMPY1Gskh0Iq16Fkiii9Yg05mnSqzTHCgn4Uo0iM.dBTbWNsIUF5ndrqLGNf4whF9-7oVTpJzEPFBYRm6ebM&dib_tag=se&qid=1747445681&s=software-intl-ship&sr=1-1"))