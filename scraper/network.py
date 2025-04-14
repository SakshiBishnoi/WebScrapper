import aiohttp
from tenacity import retry, wait_exponential, stop_after_attempt
from .proxy_manager import ProxyManager
from .user_agent_manager import UserAgentManager
import asyncio

class AsyncScraper:
    def __init__(self, config):
        self.proxy_manager = ProxyManager(config['proxies'])
        self.user_agent_manager = UserAgentManager()
        self.timeout = aiohttp.ClientTimeout(total=config.get('timeout', 30))
        self.semaphore = asyncio.Semaphore(config.get('concurrency', 10))

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def fetch(self, session, url):
        async with self.semaphore:
            proxy = self.proxy_manager.get_next_proxy()
            headers = {'User-Agent': self.user_agent_manager.get_random_user_agent()}

            async with session.get(url, proxy=proxy, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                await asyncio.sleep(self.config.get('delay', 1))
                return await response.text()

    async def fetch_all(self, urls):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)