import sys
import requests
from bs4 import BeautifulSoup
from threading import Lock, Thread
import time
from requests.exceptions import ConnectionError as fail
import random
from requests.exceptions import MissingSchema as noschema
import asyncio
from playwright.async_api import async_playwright

from pagehandler import *


user_agents = [
  "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
  "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
  "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
]


class AdminPageFinder():
    def __init__(self, base_url, playwright_instance, rate_limit=1000,request_timeout=120, batch_size = 5, headless=False):
        self.request_timeout = request_timeout*1000
        self.base_url = base_url
        self.rate_limit = 60/rate_limit
        self.lock = Lock()
        self.admin_page_list = open("lists/admin-small.txt", "r").read().split()
        self.discovered_admin_pages = set()
        self.page_handler = PageHandler(playwright_instance, headless=headless)
        self.batch_size = batch_size

    async def run(self, playwright_instance):

        for page_idx in range(0, len(self.admin_page_list), self.batch_size):

            urls = ['{}{}'.format(self.base_url, uri) for uri in self.admin_page_list[page_idx:page_idx+self.batch_size]]

            page_soups = await self.page_handler.load_pages(urls, playwright_instance)

            for page_soup, url in zip(page_soups, urls):
                if self.is_admin_page(page_soup): self.discovered_admin_pages.add(url)
        print(self.discovered_admin_pages)
            
    def is_admin_page(self, page_soup):
        return not ("404" in page_soup.title.text or "not found" in page_soup.title.text or "bad request" in page_soup.text or "something went wrong" in page_soup.text)



             
async def run():
    async with async_playwright() as playwright_instance:
#        page_handler = PageHandler(playwright_instance)
#        await page_handler.load_pages(["https://www.google.com"], playwright_instance)

        scraper = AdminPageFinder("https://www.google.com/", playwright_instance, headless=True)
        await scraper.run(playwright_instance)

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run())
    #asyncio.run(get_profile())




     
    
