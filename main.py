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
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

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
    Now with a modern, minimal, and visually appealing CLI using 'rich'.
    """
    console = Console()

    console.print(Panel(Text("Web Scraper [bold cyan]Interactive Mode[/bold cyan]", justify="center"), style="bold white on black", box=box.ROUNDED))
    console.print("[dim]Tip: Press [bold]Ctrl+C[/bold] at any time to exit.[/dim]\n")

    # Get URL
    url = Prompt.ask("[bold green]🔗 Enter URL to scrape[/bold green]", default="https://www.apple.com/shop/buy-iphone/iphone-15")
    if not url.strip():
        console.print("[red]Error: URL cannot be empty[/red]")
        return

    # Choose scraper type
    use_dynamic = Confirm.ask("[bold yellow]✨ Use dynamic scraper for JavaScript content?[/bold yellow]", default=True)

    # Get selectors
    console.print(Panel("[bold]Enter CSS selectors[/bold] (format: [cyan]key=selector[/cyan], one per line, empty line to finish)\n[dim]Or type 'auto' to use automatic content detection[/dim]", style="bold blue", box=box.SQUARE))
    selectors = {}
    while True:
        line = Prompt.ask("[grey]Selector[/grey]", default="auto" if not selectors else "")
        if not line.strip():
            break
        if line.lower() == 'auto':
            selectors = None
            break
        if '=' in line:
            key, selector = line.split('=', 1)
            selectors[key.strip()] = selector.strip()
        else:
            console.print("[red]Invalid format. Use key=selector or type 'auto'.[/red]")

    # Choose export format
    export_format = Prompt.ask("[bold magenta]📦 Export format[/bold magenta]", choices=["csv", "json"], default="json")

    # Get output filename
    output_file = Prompt.ask("[bold blue]💾 Output filename (without extension)[/bold blue]", default=f"scrape_result_{int(time.time())}")

    # Run scraper
    console.print(Panel(f"[bold green]🚀 Scraping [cyan]{url}[/cyan]...[/bold green]", style="bold green", box=box.ROUNDED))
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            task = progress.add_task("Scraping...", start=False)
            progress.start_task(task)
            time.sleep(0.3)  # Small delay for spinner effect
            if use_dynamic and dynamic_scraper:
                if selectors:
                    data = dynamic_scraper.extract_data(url, selectors)
                else:
                    data = dynamic_scraper.auto_extract(url)
            else:
                if selectors:
                    data = static_scraper.extract_data_with_selectors(url, selectors)
                else:
                    data = static_scraper.extract_data(url)
            progress.update(task, description="Exporting data...")
            time.sleep(0.2)
            if not data:
                console.print("[bold red]No data extracted[/bold red]")
                return
            if export_format == 'csv':
                file_path = exporter.export_to_csv([data], output_file)
            else:
                file_path = exporter.export_to_json(data, output_file)
        console.print(Panel(f"[bold green]✅ Data exported to:[/bold green] [cyan]{file_path}[/cyan]", style="bold green", box=box.ROUNDED))
        # Display preview
        preview = json.dumps(data, indent=2, ensure_ascii=False)
        if len(preview) > 800:
            preview = preview[:800] + "...\n[truncated]"
        console.print(Panel(preview, title="[bold]Data Preview[/bold]", style="white on black", box=box.SQUARE))
    except Exception as e:
        console.print(Panel(f"[bold red]❌ Error during scraping:[/bold red] {e}", style="bold red", box=box.ROUNDED))


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