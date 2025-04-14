#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Static Scraper Module

This module implements a scraper for static websites that don't require JavaScript
rendering. It uses requests and BeautifulSoup to fetch and parse HTML content.
"""

import logging
from typing import Dict, List, Any, Union, Optional

import requests
from bs4 import BeautifulSoup, Tag

from scraper.base import BaseScraper

logger = logging.getLogger(__name__)


class StaticScraper(BaseScraper):
    """
    Scraper for static websites that don't require JavaScript rendering.
    
    This scraper uses requests to fetch HTML content and BeautifulSoup to parse
    and extract data using CSS selectors.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the static scraper with configuration.
        
        Args:
            config: Dictionary containing scraper configuration
        """
        super().__init__(config)
    
    def extract_data(self, html_or_url: Union[str, requests.Response], selector: str = None) -> Union[List[str], Dict[str, Any]]:
        """
        Extract data from HTML content or URL using automatic content detection or provided selector.
        
        Args:
            html_or_url: HTML content as string or URL to scrape or Response object
            selector: Optional CSS selector to use for extraction
            
        Returns:
            List of extracted text or dictionary with structured content
        """
        from .content_analyzer import ContentAnalyzer
        
        # Handle URL input
        if isinstance(html_or_url, str) and (html_or_url.startswith('http://') or html_or_url.startswith('https://')):
            response = self.fetch_url(html_or_url)
            if not response:
                logger.error(f"Failed to fetch URL: {html_or_url}")
                return []
            html = response.text
            url = html_or_url
        elif isinstance(html_or_url, requests.Response):
            html = html_or_url.text
            url = html_or_url.url
        else:
            html = html_or_url
            url = None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # If no selector provided, extract all meaningful content
        if not selector:
            # First try to use content analyzer to find main content
            analyzer = ContentAnalyzer(html)
            container = analyzer.find_primary_container()
            
            # Extract all text content from the page
            extracted_content = self._extract_all_text_content(soup)
            
            logger.info(f"Extracted {len(extracted_content)} text elements from the page")
            
            # If URL was provided, return structured data
            if url:
                data = {
                    'url': url,
                    'content': extracted_content,
                    'metadata': self._extract_metadata(html)
                }
                return data
            
            # Otherwise just return the extracted text
            return extracted_content
        else:
            # Use the provided selector
            logger.info(f"Using provided selector: {selector}")
            elements = soup.select(selector)
            
            # If URL was provided, return structured data
            if url:
                data = {
                    'url': url,
                    'content': [element.get_text(strip=True) for element in elements],
                    'metadata': self._extract_metadata(html)
                }
                return data
            
            # Otherwise just return the extracted text
            return [element.get_text(strip=True) for element in elements]

    def extract_data_with_selectors(self, html_or_url: Union[str, requests.Response], selectors: Optional[dict] = None):
        """
        Extract data from a URL using the provided selectors.
        
        Args:
            url: The URL to scrape
            selectors: Dictionary mapping data keys to CSS selectors
            
        Returns:
            Dictionary containing extracted data
        """
        # Handle URL input
        if isinstance(html_or_url, str) and (html_or_url.startswith('http://') or html_or_url.startswith('https://')):
            response = self.fetch_url(html_or_url)
            if not response:
                logger.error(f"Failed to fetch URL: {html_or_url}")
                return {}
            html = response.text
            url = html_or_url
        elif isinstance(html_or_url, requests.Response):
            html = html_or_url.text
            url = html_or_url.url
        else:
            html = html_or_url
            url = "unknown"
        
        soup = self.parse_html(html)
        data = {'url': url}
        
        # If no selectors provided, use automatic content detection
        if not selectors:
            from .content_analyzer import ContentAnalyzer
            analyzer = ContentAnalyzer(html)
            container = analyzer.find_primary_container()
            if container:
                selector = container['selector']
                logger.info(f"Using automatically detected selector: {selector}")
                elements = soup.select(selector)
                data['content'] = [self._extract_element_data(el) for el in elements]
                data['metadata'] = self._extract_metadata(html)
                return data
            else:
                # Fallback to basic extraction
                data['content'] = [self._extract_element_data(soup.find('body'))]
                data['metadata'] = self._extract_metadata(html)
                return data
        
        for key, selector in selectors.items():
            try:
                # Handle different selector types (CSS, XPath, etc.)
                if selector.startswith('xpath:'):
                    # XPath selectors are not directly supported by BeautifulSoup
                    # For XPath, we would need to use lxml or another library
                    logger.warning(f"XPath selectors not implemented yet: {selector}")
                    continue
                
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
    
    def _extract_all_text_content(self, soup: BeautifulSoup) -> List[str]:
        main_content = soup.find('div', {'id': 'mw-content-text'})
        if not main_content:
            return []
        
        elements = []
        for element in main_content.find_all(['p', 'h2', 'h3', 'h4']):
            if element.name.startswith('h'):
                elements.append({'type': 'heading', 'level': int(element.name[1:]), 'text': element.get_text(strip=True)})
            else:
                elements.append({'type': 'paragraph', 'text': element.get_text(strip=True)})
        return elements    
    def _extract_element_data(self, element: Tag) -> Any:
        """
        Extract structured data from HTML elements with semantic analysis.
        Returns nested dictionaries with element type and formatted content.
        """
        element_data = {
            'type': element.name,
            'attributes': dict(element.attrs),
            'content': []
        }

        # Handle void elements differently
        if element.name in ['img', 'br', 'hr', 'input', 'meta']:
            return {'type': element.name, 'attributes': dict(element.attrs)}

        # Special handling for common semantic elements
        if element.name == 'img':
            return {
                'type': 'image',
                'src': element.get('src'),
                'alt': element.get('alt'),
                'title': element.get('title')
            }
        
        if element.name == 'a':
            return {
                'type': 'link',
                'href': element.get('href'),
                'text': element.get_text(strip=True),
                'title': element.get('title')
            }

        if element.name in ['ul', 'ol']:
            return {
                'type': 'list',
                'style': 'ordered' if element.name == 'ol' else 'unordered',
                'items': [self._extract_element_data(li) for li in element.find_all('li')]
            }

        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return {
                'type': 'heading',
                'level': int(element.name[1]),
                'text': element.get_text(strip=True)
            }

        # Recursive extraction for container elements
        if element.name in ['article', 'section', 'div', 'main', 'header', 'footer']:
            element_data['content'] = [self._extract_element_data(child) 
                                    for child in element.children 
                                    if isinstance(child, Tag)]
            return element_data

        # Default text extraction with inline semantics
        text_content = element.get_text(' ', strip=True)
        inline_elements = [self._extract_element_data(e) 
                         for e in element.find_all(['strong', 'em', 'code', 'span'])]
        
        return {
            'type': 'text',
            'value': text_content,
            'annotations': inline_elements
        }
    
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
    
    def scrape(self, urls: Union[str, List[str]], selectors: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Scrape data from one or more URLs using automatic content detection or provided selectors
        
        Args:
            urls: Single URL or list of URLs to scrape
            selectors: Optional dictionary mapping data keys to CSS selectors
            
        Returns:
            List of dictionaries with structured content
        """
        if isinstance(urls, str):
            urls = [urls]

        results = []
        for url in urls:
            logger.info(f"Scraping URL: {url}")
            
            if selectors:
                # Use provided selectors
                data = self.extract_data_with_selectors(url, selectors)
                if data:
                    results.append(data)
            else:
                # Use automatic content detection
                response = self.fetch_url(url)
                if not response:
                    continue
                    
                # Extract data using automatic content detection
                data = self.extract_data(response)
                if data:
                    results.append(data)
        
        return results
    
    def _extract_metadata(self, html):
        """Extract metadata from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {}
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Extract meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                meta_tags[meta.get('name')] = meta.get('content')
            elif meta.get('property'):
                meta_tags[meta.get('property')] = meta.get('content')
        
        if meta_tags:
            metadata['meta_tags'] = meta_tags
        
        # Extract favicon
        favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
        if favicon and favicon.get('href'):
            metadata['favicon'] = favicon.get('href')
        
        return metadata