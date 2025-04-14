#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Processor Module

This module provides functionality for processing, cleaning, and normalizing
scraped data before export or storage.
"""

import logging
import re
import json
from typing import Dict, List, Any, Union, Optional, Callable

import pandas as pd
from bs4 import BeautifulSoup

from utils.validators import validate_data_structure

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Handles processing, cleaning, and normalizing of scraped data.
    
    This class provides methods to clean, transform, and validate scraped data
    before it is exported or stored.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the data processor.
        
        Args:
            config: Configuration dictionary for data processing options
        """
        self.config = config or {}
        self.transformers = {}
        self.validators = {}
        
        logger.info("Initialized data processor")
    
    def register_transformer(self, field: str, transformer: Callable) -> None:
        """
        Register a transformer function for a specific field.
        
        Args:
            field: The field name to apply the transformer to
            transformer: Function that takes a value and returns transformed value
        """
        self.transformers[field] = transformer
        logger.debug(f"Registered transformer for field: {field}")
    
    def register_validator(self, field: str, validator: Callable) -> None:
        """
        Register a validator function for a specific field.
        
        Args:
            field: The field name to apply the validator to
            validator: Function that takes a value and returns bool (valid/invalid)
        """
        self.validators[field] = validator
        logger.debug(f"Registered validator for field: {field}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace, newlines, etc.
        
        Args:
            text: The text to clean
            
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Replace HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        
        return text
    
    def extract_text_from_html(self, html: str) -> str:
        """
        Extract plain text from HTML content.
        
        Args:
            html: HTML content as string
            
        Returns:
            Plain text extracted from HTML
        """
        if not html or not isinstance(html, str):
            return ""
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            # Get text
            text = soup.get_text()
            # Clean the text
            return self.clean_text(text)
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            return ""
    
    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize data by applying transformers and cleaning text fields.
        
        Args:
            data: Dictionary containing scraped data
            
        Returns:
            Normalized data dictionary
        """
        normalized = {}
        
        for key, value in data.items():
            # Apply registered transformer if exists
            if key in self.transformers:
                try:
                    value = self.transformers[key](value)
                except Exception as e:
                    logger.error(f"Error applying transformer for field '{key}': {str(e)}")
            
            # Clean text values
            if isinstance(value, str):
                value = self.clean_text(value)
            
            normalized[key] = value
        
        return normalized
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate data fields using registered validators.
        
        Args:
            data: Dictionary containing scraped data
            
        Returns:
            Dictionary mapping field names to validation results (True/False)
        """
        validation_results = {}
        
        for key, value in data.items():
            if key in self.validators:
                try:
                    validation_results[key] = self.validators[key](value)
                except Exception as e:
                    logger.error(f"Error applying validator for field '{key}': {str(e)}")
                    validation_results[key] = False
            else:
                # If no validator is registered, consider it valid
                validation_results[key] = True
        
        return validation_results
    
    def process_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process data by normalizing and validating it.
        
        Args:
            data: Dictionary or list of dictionaries containing scraped data
            
        Returns:
            Processed data
        """
        if isinstance(data, list):
            return [self.process_item(item) for item in data]
        else:
            return self.process_item(data)
    
    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single data item.
        
        Args:
            item: Dictionary containing scraped data
            
        Returns:
            Processed data item
        """
        # Normalize the data
        normalized = self.normalize_data(item)
        
        # Validate the data
        validation_results = self.validate_data(normalized)
        
        # Add validation metadata if configured
        if self.config.get('include_validation_metadata', False):
            normalized['_validation'] = validation_results
        
        # Filter out invalid fields if configured
        if self.config.get('filter_invalid_fields', False):
            normalized = {k: v for k, v in normalized.items() 
                         if k == '_validation' or validation_results.get(k, True)}
        
        return normalized
    
    def transform_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Transform data to pandas DataFrame for advanced processing.
        
        Args:
            data: List of dictionaries containing scraped data
            
        Returns:
            Pandas DataFrame
        """
        try:
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error transforming data to DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def filter_data(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter data based on field values.
        
        Args:
            data: List of dictionaries containing scraped data
            filters: Dictionary mapping field names to filter values
            
        Returns:
            Filtered list of data items
        """
        filtered_data = []
        
        for item in data:
            include = True
            
            for field, value in filters.items():
                if field in item:
                    # Simple equality filter
                    if item[field] != value:
                        include = False
                        break
                else:
                    include = False
                    break
            
            if include:
                filtered_data.append(item)
        
        return filtered_data
    
    def update_data(self, existing_data: List[Dict[str, Any]], new_data: List[Dict[str, Any]], 
                   key_field: str) -> List[Dict[str, Any]]:
        """
        Update existing data with new data based on a key field.
        
        Args:
            existing_data: List of existing data dictionaries
            new_data: List of new data dictionaries
            key_field: Field to use as unique identifier
            
        Returns:
            Updated list of data items
        """
        # Create a dictionary of existing data keyed by the key_field
        existing_dict = {item.get(key_field): item for item in existing_data if key_field in item}
        
        # Update existing items and add new ones
        for item in new_data:
            if key_field in item and item[key_field] in existing_dict:
                # Update existing item
                existing_dict[item[key_field]].update(item)
            elif key_field in item:
                # Add new item
                existing_dict[item[key_field]] = item
        
        return list(existing_dict.values())

    def process_content(self, raw_content: List[Dict]) -> Dict[str, Any]:
        """
        Process hierarchical content into structured format with section nesting
        """
        processed = {
            'sections': [],
            'metadata': {
                'paragraph_count': 0,
                'heading_count': 0
            }
        }

        current_section = None

        for element in raw_content:
            if element['type'].startswith('heading'):
                # New section
                current_section = {
                    'title': element['text'],
                    'level': element['level'],
                    'paragraphs': [],
                    'subsections': []
                }
                processed['sections'].append(current_section)
                processed['metadata']['heading_count'] += 1
            elif element['type'] == 'paragraph' and current_section:
                # Add to current section
                current_section['paragraphs'].append(element['text'])
                processed['metadata']['paragraph_count'] += 1

        # Merge sequential paragraphs under same section
        for section in processed['sections']:
            merged_paragraphs = []
            current_paragraph = ''
            
            for p in section['paragraphs']:
                if p.endswith(('.','!', '?')) or len(current_paragraph) > 200:
                    current_paragraph += ' ' + p
                    merged_paragraphs.append(current_paragraph.strip())
                    current_paragraph = ''
                else:
                    current_paragraph += ' ' + p
            
            if current_paragraph:
                merged_paragraphs.append(current_paragraph.strip())
            
            section['paragraphs'] = merged_paragraphs

        return processed