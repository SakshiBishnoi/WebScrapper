#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Proxy Manager Module

This module provides functionality for managing and rotating proxies
for web scraping to avoid IP blocks and distribute requests.
"""

import logging
import random
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages a pool of proxies for web scraping.
    
    This class handles proxy rotation, validation, and tracking of proxy performance
    to help avoid IP blocks and distribute requests across multiple IPs.
    """
    
    def __init__(self, proxies: List[Dict[str, str]] = None):
        """
        Initialize the proxy manager with a list of proxies.
        
        Args:
            proxies: List of proxy dictionaries with format:
                     {'http': 'http://user:pass@host:port',
                      'https': 'https://user:pass@host:port'}
        """
        self.proxies = proxies or []
        self.current_index = 0
        self.proxy_stats = {}
        
        # Initialize stats for each proxy
        for i, proxy in enumerate(self.proxies):
            proxy_id = f"proxy_{i}"
            self.proxy_stats[proxy_id] = {
                'success': 0,
                'failure': 0,
                'total_requests': 0,
                'last_used': 0
            }
        
        logger.info(f"Initialized proxy manager with {len(self.proxies)} proxies")
    
    def add_proxy(self, proxy: Dict[str, str]) -> None:
        """
        Add a new proxy to the pool.
        
        Args:
            proxy: Proxy dictionary with format:
                   {'http': 'http://user:pass@host:port',
                    'https': 'https://user:pass@host:port'}
        """
        self.proxies.append(proxy)
        proxy_id = f"proxy_{len(self.proxies) - 1}"
        self.proxy_stats[proxy_id] = {
            'success': 0,
            'failure': 0,
            'total_requests': 0,
            'last_used': 0
        }
        logger.info(f"Added new proxy to pool. Total proxies: {len(self.proxies)}")
    
    def remove_proxy(self, index: int) -> None:
        """
        Remove a proxy from the pool by index.
        
        Args:
            index: Index of the proxy to remove
        """
        if 0 <= index < len(self.proxies):
            removed = self.proxies.pop(index)
            proxy_id = f"proxy_{index}"
            if proxy_id in self.proxy_stats:
                del self.proxy_stats[proxy_id]
            
            # Adjust current index if needed
            if self.current_index >= len(self.proxies) and self.proxies:
                self.current_index = 0
                
            logger.info(f"Removed proxy at index {index}. Total proxies: {len(self.proxies)}")
        else:
            logger.warning(f"Invalid proxy index: {index}")
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get the next proxy in the rotation.
        
        Returns:
            Next proxy dictionary or None if no proxies are available
        """
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        proxy = self.proxies[self.current_index]
        proxy_id = f"proxy_{self.current_index}"
        
        # Update stats
        self.proxy_stats[proxy_id]['total_requests'] += 1
        
        # Move to next proxy for next request
        self.current_index = (self.current_index + 1) % len(self.proxies)
        
        return proxy
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get a random proxy from the pool.
        
        Returns:
            Random proxy dictionary or None if no proxies are available
        """
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        index = random.randint(0, len(self.proxies) - 1)
        proxy = self.proxies[index]
        proxy_id = f"proxy_{index}"
        
        # Update stats
        self.proxy_stats[proxy_id]['total_requests'] += 1
        
        return proxy
    
    def mark_proxy_success(self, proxy: Dict[str, str]) -> None:
        """
        Mark a proxy as having a successful request.
        
        Args:
            proxy: The proxy that was used successfully
        """
        for i, p in enumerate(self.proxies):
            if p == proxy:
                proxy_id = f"proxy_{i}"
                self.proxy_stats[proxy_id]['success'] += 1
                break
    
    def mark_proxy_failure(self, proxy: Dict[str, str]) -> None:
        """
        Mark a proxy as having a failed request.
        
        Args:
            proxy: The proxy that failed
        """
        for i, p in enumerate(self.proxies):
            if p == proxy:
                proxy_id = f"proxy_{i}"
                self.proxy_stats[proxy_id]['failure'] += 1
                break
    
    def get_proxy_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all proxies.
        
        Returns:
            Dictionary of proxy statistics
        """
        return self.proxy_stats
    
    def get_best_performing_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get the proxy with the highest success rate.
        
        Returns:
            Best performing proxy or None if no proxies are available
        """
        if not self.proxies:
            return None
        
        best_proxy_id = None
        best_success_rate = -1
        
        for proxy_id, stats in self.proxy_stats.items():
            total = stats['success'] + stats['failure']
            if total > 0:
                success_rate = stats['success'] / total
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_proxy_id = proxy_id
        
        if best_proxy_id is not None:
            index = int(best_proxy_id.split('_')[1])
            return self.proxies[index]
        
        # If no proxy has been used yet, return the first one
        return self.proxies[0]