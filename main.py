#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web Scraper with GUI - Main Application Entry Point

This module serves as the entry point for the Web Scraper application.
It initializes the core scraping functionality (Phase 1 & 2) and provides
a command-line interface for interacting with the scraper.
"""

import os
import sys
import json
import logging
import argparse
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command line arguments for the scraper.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(description="Web Scraper CLI")
    parser.add_argument("-u", "--url", help="URL to scrape")
    parser.add_argument("-s", "--selectors", help="JSON string or path to JSON file with CSS selectors")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", choices=["csv", "json"], default="json", help="Output format (default: json)")
    parser.add_argument("-d", "--dynamic", action="store_true", help="Use dynamic scraper for JavaScript-heavy sites")
    parser.add_argument("-c", "--config", help="Path to custom configuration file")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    return parser.parse_args()


def load_selectors(selectors_input: str) -> Dict[str, str]:
    """
    Load selectors from a JSON string or file.
    
    Args:
        selectors_input: JSON string or path to JSON file
        
    Returns:
        Dictionary of selectors
    """
    if os.path.isfile(selectors_input):
        try:
            with open(selectors_input, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading selectors from file: {e}")
            return {}
    else:
        try:
            return json.loads(selectors_input)
        except Exception as e:
            logger.error(f"Error parsing selectors JSON: {e}")
            return {}


def interactive_mode(static_scraper, dynamic_scraper, exporter):
    """
    Run the scraper in interactive mode, prompting the user for input.
    
    Args:
        static_scraper: Static scraper instance
        dynamic_scraper: Dynamic scraper instance
        exporter: Data exporter instance
    """
    print("\nInteractive Mode")
    print("===============")
    
    # Get URL
    url = input("Enter URL to scrape: ").strip()
    if not url:
        print("Error: URL cannot be empty")
        return
    
    # Choose scraper type
    use_dynamic = input("Use dynamic scraper for JavaScript content? (y/n): ").lower().startswith('y')
    
    # Get selectors
    print("\nEnter CSS selectors (format: key=selector, one per line, empty line to finish)")
    print("Or type 'auto' to use automatic content detection:")
    selectors = {}
    while True:
        line = input("> ").strip()
        if not line:
            break
        
        if line.lower() == 'auto':
            # Use automatic content detection
            selectors = None
            break
        
        if '=' in line:
            key, selector = line.split('=', 1)
            selectors[key.strip()] = selector.strip()
    
    # Choose export format
    export_format = input("\nExport format (csv/json): ").lower()
    if export_format not in ['csv', 'json']:
        export_format = 'json'
    
    # Get output filename
    output_file = input("Output filename (without extension): ").strip()
    if not output_file:
        output_file = f"scrape_result_{int(time.time())}"
    
    # Run scraper
    print(f"\nScraping {url}...")
    try:
        if use_dynamic and dynamic_scraper:
            if selectors:
                data = dynamic_scraper.extract_data(url, selectors)
            else:
                # Use smart automatic content detection
                data = dynamic_scraper.auto_extract(url)
        else:
            if selectors:
                data = static_scraper.extract_data_with_selectors(url, selectors)
            else:
                # Use automatic content detection
                data = static_scraper.extract_data(url)
        
        if not data:
            print("No data extracted")
            return
        
        # Export data
        if export_format == 'csv':
            file_path = exporter.export_to_csv([data], output_file)
        else:
            file_path = exporter.export_to_json(data, output_file)
        
        print(f"\nData exported to: {file_path}")
        
        # Display preview
        print("\nData Preview:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error during scraping: {e}")


def main():
    """
    Main function to start the application.
    """
    try:
        logger.info("Starting Web Scraper application")
        
        # Parse command line arguments
        args = parse_arguments()
        
        # Import scraper components with error handling for missing dependencies
        try:
            # Load configuration
            if args.config:
                config_path = args.config
            else:
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'default_config.json')
            
            with open(config_path, 'r') as f:
                config = json.loads(f.read())
            
            # Import core components
            from scraper.static import StaticScraper
            static_scraper = StaticScraper(config)
            logger.info("Static scraper initialized successfully")
            
            dynamic_scraper = None
            try:
                from scraper.dynamic import DynamicScraper
                dynamic_scraper = DynamicScraper(config)
                logger.info("Dynamic scraper initialized successfully")
            except ImportError as e:
                logger.warning(f"Dynamic scraper could not be initialized: {e}")
                logger.warning("Some dependencies may be missing. Run 'pip install -r requirements.txt' to install all dependencies.")
            
            from utils.data_export import DataExporter
            exporter = DataExporter()
            logger.info("Data exporter initialized successfully")
            
            # Import data processor
            try:
                from utils.data_processor import DataProcessor
                processor = DataProcessor()
                logger.info("Data processor initialized successfully")
            except ImportError as e:
                logger.warning(f"Data processor could not be initialized: {e}")
                processor = None
            
        except Exception as e:
            logger.warning(f"Could not initialize all scraper components: {e}")
            logger.warning("This is expected during Phase 2 development if not all dependencies are installed.")
            logger.warning("Run 'pip install -r requirements.txt' to install all dependencies.")
            return 1
        
        # Display application header
        print("Web Scraper with GUI")
        print("====================")
        print("\nCurrently in Phase 2: Core Scraping Functionality")
        print("GUI will be implemented in Phase 3.")
        
        # Run in interactive mode if requested
        if args.interactive:
            interactive_mode(static_scraper, dynamic_scraper, exporter)
            return 0
        
        # Process command line arguments for direct scraping
        if args.url:
            # Load selectors
            selectors = {}
            if args.selectors:
                selectors = load_selectors(args.selectors)
                if not selectors:
                    logger.error("Failed to load selectors")
                    return 1
            else:
                logger.error("No selectors provided")
                print("Error: Please provide selectors using -s/--selectors option")
                return 1
            
            # Run appropriate scraper
            logger.info(f"Scraping URL: {args.url}")
            try:
                if args.dynamic and dynamic_scraper:
                    data = dynamic_scraper.extract_data(args.url, selectors)
                else:
                    data = static_scraper.extract_data(args.url, selectors)
                
                if not data:
                    logger.warning("No data extracted")
                    print("No data was extracted from the URL")
                    return 1
                
                # Process data if processor is available
                if processor:
                    data = processor.process_data(data)
                
                # Export data
                if args.output:
                    output_file = args.output
                else:
                    output_file = f"scrape_result_{int(time.time())}"
                if args.format in ['csv', 'json']:
                    file_path = exporter.export_data(data, output_file, args.format)
                else:
                    file_path = exporter.export_to_json(data, output_file)
                
                logger.info(f"Data exported to: {file_path}")
                print(f"\nData exported to: {file_path}")
                
                # Display preview
                print("\nData Preview:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2, ensure_ascii=False))
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}", exc_info=True)
                print(f"Error during scraping: {e}")
                return 1
        else:
            # No URL provided, show usage
            print("\nUsage Examples:")
            print("  1. Interactive mode: python main.py --interactive")
            print("  2. Direct scraping: python main.py -u https://example.com -s \"{\"title\": \"h1\", \"paragraphs\": \"p\"}\" -f json")
            print("  3. Using selectors file: python main.py -u https://example.com -s selectors.json -o results -f csv")
            print("\nRun 'python main.py -h' for more information.")
        
        logger.info("Application completed successfully")
        
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())