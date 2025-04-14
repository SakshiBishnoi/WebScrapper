#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dynamic Scraper Module

This module implements a scraper for dynamic websites that require JavaScript
rendering. It uses Selenium WebDriver to load and interact with web pages.
"""

import logging
import time
from typing import Dict, List, Any, Union, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, Tag

from scraper.base import BaseScraper

logger = logging.getLogger(__name__)


class DynamicScraper(BaseScraper):
    """
    Scraper for dynamic websites that require JavaScript rendering.
    
    This scraper uses Selenium WebDriver to load and interact with web pages,
    allowing it to handle JavaScript-rendered content.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the dynamic scraper with configuration.
        
        Args:
            config: Dictionary containing scraper configuration
        """
        super().__init__(config)
        
        self.browser_config = config.get('browser', {})
        self.headless = self.browser_config.get('headless', True)
        self.window_size = self.browser_config.get('window_size', [1920, 1080])
        self.implicit_wait = self.browser_config.get('implicit_wait', 10)
        self.page_load_timeout = self.browser_config.get('page_load_timeout', 30)
        self.script_timeout = self.browser_config.get('script_timeout', 30)
        
        self.driver = None
        self.initialized = False
    
    def _initialize_driver(self):
        """
        Initialize the Selenium WebDriver with configured options.
        """
        if self.initialized and self.driver:
            return
        
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless')
            
            options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
            options.add_argument('--disable-gpu')  # Required for Windows
            options.add_argument('--no-sandbox')  # Required for running in Docker
            options.add_argument('--disable-dev-shm-usage')  # Required for running in Docker
            
            # Set user agent if provided
            if 'user_agent' in self.config:
                options.add_argument(f'--user-agent={self.config["user_agent"]}')
            
            # Initialize the WebDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Set timeouts
            self.driver.implicitly_wait(self.implicit_wait)
            self.driver.set_page_load_timeout(self.page_load_timeout)
            self.driver.set_script_timeout(self.script_timeout)
            
            self.initialized = True
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            raise
    
    def _close_driver(self):
        """
        Close the Selenium WebDriver.
        """
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing Selenium WebDriver: {e}")
            finally:
                self.driver = None
                self.initialized = False
    
    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL using Selenium WebDriver.
        
        Args:
            url: The URL to fetch
            
        Returns:
            HTML content as string or None if failed
        """
        self._respect_rate_limit()
        
        if not self.initialized:
            self._initialize_driver()
        
        for attempt in range(self.retry_count + 1):
            try:
                logger.info(f"Fetching URL with Selenium: {url} (Attempt {attempt + 1}/{self.retry_count + 1})")
                self.driver.get(url)
                
                # Wait for page to load completely
                WebDriverWait(self.driver, self.page_load_timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                # Additional wait to allow JavaScript to render content
                time.sleep(2)
                
                return self.driver.page_source
                
            except (TimeoutException, WebDriverException) as e:
                logger.warning(f"Selenium request failed: {e}")
                if attempt < self.retry_count:
                    sleep_time = self.retry_delay * (attempt + 1)
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All retry attempts failed for URL: {url}")
                    return None
    
    def extract_data(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract data from a URL using the provided selectors.
        
        Args:
            url: The URL to scrape
            selectors: Dictionary mapping data keys to CSS/XPath selectors
            
        Returns:
            Dictionary containing extracted data
        """
        html_content = self.fetch_url(url)
        if not html_content:
            logger.error(f"Failed to fetch URL: {url}")
            return {}
        
        soup = self.parse_html(html_content)
        data = {'url': url}
        
        for key, selector in selectors.items():
            try:
                elements = []
                
                # Handle different selector types
                if selector.startswith('xpath:'):
                    xpath = selector[6:]  # Remove 'xpath:' prefix
                    if self.driver:
                        selenium_elements = self.driver.find_elements(By.XPATH, xpath)
                        html_elements = [element.get_attribute('outerHTML') for element in selenium_elements]
                        for html in html_elements:
                            elements.extend(BeautifulSoup(html, 'html.parser').contents)
                else:
                    # Default to CSS selectors
                    elements = soup.select(selector)
                
                if not elements:
                    logger.warning(f"No elements found for selector '{selector}' (key: {key})")
                    data[key] = None
                    continue
                
                # Extract data based on the number of elements found
                if len(elements) == 1:
                    data[key] = self._extract_element_data(elements[0])
                else:
                    data[key] = [self._extract_element_data(el) for el in elements]
                    
            except Exception as e:
                logger.error(f"Error extracting data for key '{key}': {e}")
                data[key] = None
        
        return data
    
    def _extract_element_data(self, element: Tag) -> Any:
        """
        Extract data from a BeautifulSoup element based on its type.
        
        Args:
            element: BeautifulSoup Tag object
            
        Returns:
            Extracted data (text, attributes, etc.)
        """
        # For images, return the src attribute
        if element.name == 'img':
            return {'src': element.get('src'), 'alt': element.get('alt'), 'text': element.get_text(strip=True)}
        
        # For links, return the href attribute and text
        elif element.name == 'a':
            return {'href': element.get('href'), 'text': element.get_text(strip=True)}
        
        # For tables, convert to a list of dictionaries
        elif element.name == 'table':
            return self._parse_table(element)
        
        # For other elements, return the text content
        else:
            return element.get_text(strip=True)
    
    def _parse_table(self, table: Tag) -> List[Dict[str, str]]:
        """
        Parse an HTML table into a list of dictionaries.
        
        Args:
            table: BeautifulSoup Tag object representing a table
            
        Returns:
            List of dictionaries, each representing a row with column headers as keys
        """
        result = []
        
        # Extract headers
        headers = []
        header_row = table.find('thead')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        
        # If no headers found in thead, try the first row
        if not headers:
            first_row = table.find('tr')
            if first_row:
                headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
        
        # If still no headers, use generic column names
        if not headers:
            # Find the row with the most columns to determine the number of columns
            rows = table.find_all('tr')
            max_cols = max([len(row.find_all(['td', 'th'])) for row in rows]) if rows else 0
            headers = [f"Column {i+1}" for i in range(max_cols)]
        
        # Extract rows
        for row in table.find_all('tr'):
            # Skip header row if it's the same as the one we already processed
            cells = row.find_all(['td', 'th'])
            if cells and ([cell.get_text(strip=True) for cell in cells] != headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text(strip=True)
                if row_data:
                    result.append(row_data)
        
        return result
    
    def scrape(self, urls: Union[str, List[str]], selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Scrape data from one or more URLs.
        
        Args:
            urls: Single URL or list of URLs to scrape
            selectors: Dictionary mapping data keys to CSS/XPath selectors
            
        Returns:
            List of dictionaries containing extracted data
        """
        if isinstance(urls, str):
            urls = [urls]
        
        try:
            self._initialize_driver()
            
            results = []
            for url in urls:
                logger.info(f"Scraping URL with Selenium: {url}")
                data = self.extract_data(url, selectors)
                if data:
                    results.append(data)
            
            return results
            
        finally:
            self._close_driver()
    
    def __del__(self):
        """
        Ensure the WebDriver is closed when the object is garbage collected.
        """
        self._close_driver()