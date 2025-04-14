#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
User Agent Manager Module

This module provides functionality for managing and rotating user agents
for web scraping to avoid detection and blocks.
"""

import logging
import random
from typing import List, Optional

logger = logging.getLogger(__name__)


class UserAgentManager:
    """
    Manages a pool of user agents for web scraping.
    
    This class handles user agent rotation to help avoid detection
    and blocks by websites during scraping operations.
    """
    
    # Common user agents for different browsers and platforms
    DEFAULT_USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        # Mobile Chrome on Android
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        # Mobile Safari on iOS
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    
    def __init__(self, user_agents: List[str] = None):
        """
        Initialize the user agent manager with a list of user agents.
        
        Args:
            user_agents: List of user agent strings. If None, default list is used.
        """
        self.user_agents = user_agents or self.DEFAULT_USER_AGENTS
        self.current_index = 0
        
        logger.info(f"Initialized user agent manager with {len(self.user_agents)} user agents")
    
    def add_user_agent(self, user_agent: str) -> None:
        """
        Add a new user agent to the pool.
        
        Args:
            user_agent: User agent string to add
        """
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)
            logger.info(f"Added new user agent to pool. Total user agents: {len(self.user_agents)}")
        else:
            logger.warning(f"User agent already exists in pool: {user_agent}")
    
    def remove_user_agent(self, user_agent: str) -> None:
        """
        Remove a user agent from the pool.
        
        Args:
            user_agent: User agent string to remove
        """
        if user_agent in self.user_agents:
            self.user_agents.remove(user_agent)
            
            # Adjust current index if needed
            if self.current_index >= len(self.user_agents) and self.user_agents:
                self.current_index = 0
                
            logger.info(f"Removed user agent from pool. Total user agents: {len(self.user_agents)}")
        else:
            logger.warning(f"User agent not found in pool: {user_agent}")
    
    def get_next_user_agent(self) -> Optional[str]:
        """
        Get the next user agent in the rotation.
        
        Returns:
            Next user agent string or None if no user agents are available
        """
        if not self.user_agents:
            logger.warning("No user agents available")
            return None
        
        user_agent = self.user_agents[self.current_index]
        
        # Move to next user agent for next request
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        
        return user_agent
    
    def get_random_user_agent(self) -> Optional[str]:
        """
        Get a random user agent from the pool.
        
        Returns:
            Random user agent string or None if no user agents are available
        """
        if not self.user_agents:
            logger.warning("No user agents available")
            return None
        
        return random.choice(self.user_agents)
    
    def get_all_user_agents(self) -> List[str]:
        """
        Get all user agents in the pool.
        
        Returns:
            List of all user agent strings
        """
        return self.user_agents.copy()
    
    def clear_user_agents(self) -> None:
        """
        Clear all user agents from the pool.
        """
        self.user_agents = []
        self.current_index = 0
        logger.info("Cleared all user agents from pool")
    
    def reset_to_defaults(self) -> None:
        """
        Reset the user agent pool to the default list.
        """
        self.user_agents = self.DEFAULT_USER_AGENTS.copy()
        self.current_index = 0
        logger.info(f"Reset user agent pool to defaults. Total user agents: {len(self.user_agents)}")