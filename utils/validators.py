#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Validators Module

This module provides validation functions for various inputs to the Web Scraper application.
It includes validators for URLs, selectors, configuration parameters, and data structures.
"""

import re
import logging
import json
from typing import Dict, List, Any, Union, Optional, Callable
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate if a string is a properly formatted URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        return False


def validate_selector(selector: str) -> bool:
    """
    Validate if a string is a properly formatted CSS selector.
    
    Args:
        selector: The CSS selector string to validate
        
    Returns:
        True if the selector is valid, False otherwise
    """
    # Basic validation - more complex validation would require a CSS parser
    if not selector or not isinstance(selector, str):
        return False
    

def validate_data_structure(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate data against a schema definition.
    
    Args:
        data: The data to validate
        schema: Schema definition dictionary
        
    Returns:
        True if the data is valid according to the schema, False otherwise
    """
    try:
        # Check type
        if 'type' in schema:
            if schema['type'] == 'object' and not isinstance(data, dict):
                logger.debug(f"Expected object, got {type(data).__name__}")
                return False
            elif schema['type'] == 'array' and not isinstance(data, list):
                logger.debug(f"Expected array, got {type(data).__name__}")
                return False
            elif schema['type'] == 'string' and not isinstance(data, str):
                logger.debug(f"Expected string, got {type(data).__name__}")
                return False
            elif schema['type'] == 'number' and not isinstance(data, (int, float)):
                logger.debug(f"Expected number, got {type(data).__name__}")
                return False
            elif schema['type'] == 'boolean' and not isinstance(data, bool):
                logger.debug(f"Expected boolean, got {type(data).__name__}")
                return False
        
        # Check required fields for objects
        if isinstance(data, dict) and 'required' in schema:
            for field in schema['required']:
                if field not in data:
                    logger.debug(f"Required field '{field}' missing")
                    return False
        
        # Check properties for objects
        if isinstance(data, dict) and 'properties' in schema:
            for field, field_schema in schema['properties'].items():
                if field in data and data[field] is not None:
                    if not validate_data_structure(data[field], field_schema):
                        logger.debug(f"Field '{field}' failed validation")
                        return False
        
        # Check items for arrays
        if isinstance(data, list) and 'items' in schema:
            for item in data:
                if not validate_data_structure(item, schema['items']):
                    logger.debug("Array item failed validation")
                    return False
        
        # Check enum values
        if 'enum' in schema and data not in schema['enum']:
            logger.debug(f"Value {data} not in enum {schema['enum']}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating data structure: {str(e)}")
        return False
    
    # Check for common syntax errors
    invalid_patterns = [
        r'[\[\]\(\)\{\}](?![^"]*"[^"]*(?:"[^"]*"[^"]*)*$)',  # Unbalanced brackets
        r'[#\.][#\.]',  # Double class or ID indicators
        r':[^:]+'  # Invalid pseudo-class
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, selector):
            return False
    
    return True


def validate_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate scraper configuration parameters.
    
    Args:
        config: Dictionary containing configuration parameters
        
    Returns:
        Dictionary with validation errors by parameter
    """
    errors = {}
    
    # Required fields
    required_fields = ['headers', 'timeout', 'retry_count']
    for field in required_fields:
        if field not in config:
            if 'missing' not in errors:
                errors['missing'] = []
            errors['missing'].append(field)
    
    # Type validation
    if 'timeout' in config and not isinstance(config['timeout'], (int, float)):
        if 'type' not in errors:
            errors['type'] = []
        errors['type'].append('timeout must be a number')
    
    if 'retry_count' in config and not isinstance(config['retry_count'], int):
        if 'type' not in errors:
            errors['type'] = []
        errors['type'].append('retry_count must be an integer')
    
    if 'headers' in config and not isinstance(config['headers'], dict):
        if 'type' not in errors:
            errors['type'] = []
        errors['type'].append('headers must be a dictionary')
    
    # Value validation
    if 'timeout' in config and isinstance(config['timeout'], (int, float)) and config['timeout'] <= 0:
        if 'value' not in errors:
            errors['value'] = []
        errors['value'].append('timeout must be positive')
    
    if 'retry_count' in config and isinstance(config['retry_count'], int) and config['retry_count'] < 0:
        if 'value' not in errors:
            errors['value'] = []
        errors['value'].append('retry_count must be non-negative')
    
    return errors


def validate_export_format(format_type: str) -> bool:
    """
    Validate if the export format is supported.
    
    Args:
        format_type: The export format to validate
        
    Returns:
        True if the format is supported, False otherwise
    """
    supported_formats = ['csv', 'json']
    return format_type.lower() in supported_formats