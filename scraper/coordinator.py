import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from .network import AsyncScraper
from .storage import DataStorage
from .dynamic import DynamicContentScraper
import logging

class ScrapingCoordinator:
    def __init__(self, config):
        self.config = config
        self.scraper = AsyncScraper(config)
        self.storage = DataStorage(config)
        self.dynamic_scraper = DynamicContentScraper(config) if config.get('js_rendering') else None
        self.logger = logging.getLogger(__name__)
        
    async def run(self, urls):
        """Main entry point for scraping operations"""
        try:
            html_responses = await self.scraper.fetch_all(urls)
            processed_data = await self._process_responses(html_responses)
            self.storage.save(processed_data, self.config['output_file'])
            return True
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
    async def _process_responses(self, responses):
        """Process HTML responses with appropriate parser"""
        processed_data = []
        for html in responses:
            if not html or isinstance(html, Exception):
                continue
                
            if self.dynamic_scraper:
                data = await self.dynamic_scraper.extract(html)
            else:
                data = self._static_extraction(html)
            
            if data:
                processed_data.extend(data)
        return processed_data

    def _static_extraction(self, html):
        """Placeholder for static content extraction logic"""
        # Implementation would use BeautifulSoup/lxml
        return []

    async def shutdown(self):
        """Cleanup resources"""
        await self.scraper.close()
        if self.dynamic_scraper:
            await self.dynamic_scraper.close()