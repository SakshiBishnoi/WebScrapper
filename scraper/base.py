#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base Scraper Module

This module defines the base scraper class that provides common functionality
for all scraper types. It handles request management, error handling, and
basic data extraction.
"""

import logging
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, ProxyError

from scraper.proxy_manager import ProxyManager
from scraper.user_agent_manager import UserAgentManager

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for all scrapers providing common functionality.
    
    This abstract class defines the interface and common methods for all
    scraper implementations. Specific scraper types (static, dynamic) will
    inherit from this class and implement the abstract methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the base scraper with configuration.
        
        Args:
            config: Dictionary containing scraper configuration
        """
        self.config = config
        self.headers = config.get('headers', {})
        self.timeout = config.get('timeout', 30)
        self.retry_count = config.get('retry_count', 3)
        self.retry_delay = config.get('retry_delay', 5)
        self.respect_robots_txt = config.get('respect_robots_txt', True)
        self.rate_limit = config.get('rate_limit', {'requests_per_minute': 20, 'pause_between_requests': 3})
        
        # Initialize proxy manager if proxies are provided
        proxy_config = config.get('proxies', [])
        self.proxy_manager = ProxyManager(proxy_config) if proxy_config else None
        self.use_proxies = bool(proxy_config) and config.get('use_proxies', False)
        
        # Initialize user agent manager
        user_agents = config.get('user_agents', [])
        self.user_agent_manager = UserAgentManager(user_agents)
        self.rotate_user_agents = config.get('rotate_user_agents', False)
        
        # Set default user agent if not provided
        if 'user_agent' in config and 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = config['user_agent']
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Last request timestamp for rate limiting
        self.last_request_time = 0
        
        # Cookie management
        self.use_cookies = config.get('use_cookies', True)
        if not self.use_cookies:
            self.session.cookies.clear()
    
    def _respect_rate_limit(self):
        """
        Ensure rate limiting by pausing between requests if needed.
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.rate_limit['pause_between_requests']:
            sleep_time = self.rate_limit['pause_between_requests'] - elapsed
            logger.debug(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _update_user_agent(self):
        """
        Update the user agent in the session headers if rotation is enabled.
        """
        if self.rotate_user_agents:
            user_agent = self.user_agent_manager.get_random_user_agent()
            if user_agent:
                self.session.headers.update({'User-Agent': user_agent})
                logger.debug(f"Rotated user agent to: {user_agent}")
    
    def _get_proxy(self):
        """
        Get a proxy from the proxy manager if proxy usage is enabled.
        
        Returns:
            Proxy dictionary or None
        """
        if self.use_proxies and self.proxy_manager:
            return self.proxy_manager.get_random_proxy()
        return None
    
    def fetch_url(self, url: str) -> Optional[requests.Response]:
        """
        Fetch content from a URL with retry logic, rate limiting, and proxy/user-agent rotation.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Response object or None if all retries failed
        """
        self._respect_rate_limit()
        
        # Update user agent before request if rotation is enabled
        self._update_user_agent()
        
        for attempt in range(self.retry_count + 1):
            # Get proxy for this attempt
            proxy = self._get_proxy() if self.use_proxies else None
            
            try:
                logger.info(f"Fetching URL: {url} (Attempt {attempt + 1}/{self.retry_count + 1})")
                if proxy:
                    logger.debug(f"Using proxy: {proxy}")
                    response = self.session.get(url, timeout=self.timeout, proxies=proxy)
                else:
                    response = self.session.get(url, timeout=self.timeout)
                
                response.raise_for_status()
                
                # Mark proxy as successful if used
                if proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_success(proxy)
                
                return response
                
            except ProxyError as e:
                logger.warning(f"Proxy error: {e}")
                # Mark proxy as failed
                if proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_failure(proxy)
                
                # Try again immediately with a different proxy
                continue
                
            except RequestException as e:
                logger.warning(f"Request failed: {e}")
                
                # Mark proxy as failed if used
                if proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_failure(proxy)
                
                if attempt < self.retry_count:
                    sleep_time = self.retry_delay * (attempt + 1)
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All retry attempts failed for URL: {url}")
                    return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'html.parser')
    
    @abstractmethod
    def extract_data(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract data from a URL using the provided selectors.
        
        Args:
            url: The URL to scrape
            selectors: Dictionary mapping data keys to CSS/XPath selectors
            
        Returns:
            Dictionary containing extracted data
        """
        pass
    
    @abstractmethod
    def scrape(self, urls: Union[str, List[str]], selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Scrape data from one or more URLs.
        
        Args:
            urls: Single URL or list of URLs to scrape
            selectors: Dictionary mapping data keys to CSS/XPath selectors
            
        Returns:
            List of dictionaries containing extracted data
        """
        pass