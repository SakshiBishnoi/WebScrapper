#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Export Module

This module provides functionality for exporting scraped data to various formats
including CSV and JSON. It handles formatting, validation, and file operations.
"""

import csv
import json
import os
import logging
from typing import Dict, List, Any, Union, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Handles exporting scraped data to various file formats.
    
    This class provides methods to export data to CSV and JSON formats,
    with options for formatting and validation.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the data exporter.
        
        Args:
            output_dir: Directory where exported files will be saved
        """
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'exports')
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Export directory verified: {os.path.abspath(self.output_dir)}")
        logger.debug(f"Full export path: {os.path.abspath(os.path.join(self.output_dir, 'test'))}")
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str, 
                      headers: Optional[List[str]] = None) -> str:
        """
        Export data to CSV format.
        
        Args:
            data: List of dictionaries containing the data to export
            filename: Name of the output file (without extension)
            headers: Optional list of column headers
            
        Returns:
            Path to the exported file
        """
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # If headers not provided, use keys from first data item
            if not headers and data:
                headers = list(data[0].keys())
            
            # Use pandas for more complex CSV operations
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, header=headers is not None)
            
            logger.info(f"Successfully exported data to CSV: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to export data to CSV: {str(e)}")
            raise
    
    def export_to_json(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], 
                       filename: str, pretty: bool = True) -> str:
        """
        Export data to JSON format.
        
        Args:
            data: Data to export (list of dictionaries or single dictionary)
            filename: Name of the output file (without extension)
            pretty: Whether to format the JSON with indentation
            
        Returns:
            Path to the exported file
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            logger.info(f"Successfully exported data to JSON: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to export data to JSON: {str(e)}")
            raise
    
    def export_data(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], 
                   filename: str, format_type: str = 'json') -> str:
        # Validate data before exporting
        if not data:
            logger.error("Cannot export empty dataset")
            raise ValueError("Empty data received for export")

        # Validate filename
        if not filename.strip():
            logger.error("Empty filename provided")
            raise ValueError("Filename cannot be empty")
        """
        Export data to the specified format.
        
        Args:
            data: Data to export
            filename: Name of the output file (without extension)
            format_type: Format to export to ('csv' or 'json')
            
        Returns:
            Path to the exported file
        """
        format_type = format_type.lower()
        
        if format_type == 'csv':
            # Ensure data is a list of dictionaries for CSV export
            if isinstance(data, dict):
                data = [data]
            return self.export_to_csv(data, filename)
        
        elif format_type == 'json':
            return self.export_to_json(data, filename)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")