from bs4 import BeautifulSoup
from threading import Lock
import time
import random
import asyncio
from playwright.async_api import async_playwright
import re
from urllib.parse import urlparse
import sys

from websitemap import *
from pagehandler import *
from urlhandler import *





class EmailFilter():
    def __init__(self):
        self.tld_whitelist = ['hosting', 'org', 'orgspca', 'vet', 'pro', 'us', 'dk', 'com', 'cat', 'pet', 'services', 
                            'io',  'al', 'it', 'gov', 'business', 'pharmacy', 'co', 'in', 'net', 'edu', 'biz', 'com','la', 
                            'su', 'web', 'info', 'clinic', 'cnet', 'me', 'today', 'de', 'gg', 'one', 'agency', 'dog', 'nvanet', 'site', "pr"]
        self.email_domain_name_blacklist = ["@domain.com", "@yourdomain" ,"@yourshop" ,"@yourcompanydomain", "@mydomain", "noreply", "notreply", "@example", "@email", "@sentry"]

    def is_valid_email(self, email):

        email_name = email.split("@")[0]

        if email == None: return False

        #email name blacklist (privacy, news, help, noreply, ...)
        #for keyword in self.email_name_blacklist:
        #    if keyword == email_name: return False


        #email domain name blacklist (@example, @mail.com, @domain.com, ...)
        for keyword in self.email_domain_name_blacklist:
            if keyword in email: return False

        tld = email.split(".")[-1]
        if not tld in self.tld_whitelist: return False

        return True



class LinkExtractor():
    def __init__(self, base_url, page_handler, headless=False, debug=False):
        self.page_handler = page_handler
        self.base_url = base_url
        self.url_handler = UrlHandler(base_url)
        self.email_re = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
        self.collected_emails = set()
        self.email_filter = EmailFilter()


    def set_url_handler(self, url_handler):
        self.url_handler = url_handler 

    def set_base_url(self, url):
        self.url_handler = url
        self.url_handler.set_base_url(url)

    async def extract_from_pages(self, urls):
        #load page
        page_soups = await self.page_handler.load_pages(urls)

        links = self.extract_links_from_pages(page_soups)

        emails = self.extract_emails_from_pages(page_soups)

        return links, emails


    #extract links from a list of urls
    def extract_links_from_pages(self, page_soups):

        links = set()
        for soup in page_soups:
            if soup == None:
                continue
                
            for link in self.extract_links(soup):
                links.add(link)
       
        return links


    #extracts links from an invidivual soup obj
    def extract_links(self, soup):
        #extract all links from every page
        if soup == None: return None
        links = soup.find_all('a')

        extracted_links = set()

        for link in links:
            try:
                url = self.url_handler.fix_url(link.attrs['href'])
                if self.url_handler.is_valid_url(url): extracted_links.add(url)
            except:
                continue

        return extracted_links

    def extract_emails_from_pages(self, soups):
        return set([email for email in self.extract_emails_from_page([soup for soup in soups]) if self.email_filter.is_valid_email(email)])

    def extract_emails_from_page(self, soup):
        emails = set()

        #extract emails from home page
        time1 = time.time()

        cleaned_html = [self.remove_tags(html) for html in soup if html != None]

        unique_found_emails = [email for email in self.email_re.findall(str(cleaned_html)) if email not in self.collected_emails]
        
        #add unique emails to found emails
        emails.update(unique_found_emails)

        return emails

    def remove_tags(self, soup):
        for data in soup.findAll("style"):
            # Remove tags
            if data != None: data.decompose()
      
            # return data by retrieving the tag content
        try:
            return ''.join(str(soup))
        except:
            return None




#scrapes the entire website 
class WebSpider():
    def __init__(self, base_url, playwright_instance, cookies=None, headless=False, debug=False):

        #base url to start spider
        self.base_url = base_url

        #page handler object for opening pages and handling browsers
        self.page_handler = PageHandler(playwright_instance, cookies=cookies, headless=headless, debug=debug )

        #link extractor object for extracting links from a page
        self.link_extractor = LinkExtractor(base_url, self.page_handler, headless=False, debug=False)

        #website map object
        self.webmap = WebsiteMap()

        self.queued_links = set([base_url])

        self.unique_urls = set()

        self.lock = Lock()

    def set_url_handler(self, url_handler):
        self.link_extractor.set_url_handler(url_handler)

    def get_emails(self):
        return self.link_extractor.collected_emails()
    
    def get_base_url(self):
        return self.base_url

    def set_base_url(self, url):
        self.base_url = url
        self.link_extractor.set_base_url(url)

    def get_next_url(self):
        
        self.lock.acquire()
        try:
            url = self.queued_links.pop()
            
            #get the next non-visited url
            while self.webmap.visited(url, strict=False):
                url = self.queued_links.pop()

            self.lock.release()
            return url
        except:
            self.lock.release()

            return None

    async def crawl(self):

        while len(self.queued_links) > 0:

            #extract links  
            urls = [self.get_next_url() for url in range(5)]

            extracted_links, emails = await self.link_extractor.extract_from_pages(urls)

            print(emails)

            #may need to take care of redirected links so theres no infinite loops
            self.webmap.add_entries(urls)

            self.update_visited_links(extracted_links)

            self.log_to_file()

        return self.unique_urls
    
    def log_to_file(self):
        f = open("sites.txt", "w")

        for line in self.unique_urls:
            f.write(line)
            f.write("\n")

        f.close()

    def update_visited_links(self, extracted_links):
            self.lock.acquire()

            #update links with only the urls that arent already visited
            self.queued_links.update(set(url for url in extracted_links if not self.webmap.visited(url, strict=False)))

            self.unique_urls.update(set(url for url in extracted_links if not self.webmap.visited(url, strict=False)))

            print("Total visited: {}\nLinks Queued: {}".format(len(self.unique_urls), len(self.queued_links)))

            self.lock.release()

    def load_state(self, visited_urls=None, additional_start_domains=None):
        print("Loading state ...")

        if additional_start_domains != None:
            with open(additional_start_domains) as file:
                additional_start_domains = [line.rstrip() for line in file]

            self.queued_links.update(set(additional_start_domains))
            self.unique_urls.update(set(additional_start_domains))

            print("Queued {} subdomains".format(len(additional_start_domains)))


        if visited_urls != None:
            with open(visited_urls) as file:
                 visited_urls = [line.rstrip() for line in file]

            self.webmap.add_entries(visited_urls)
            self.unique_urls.update(set(visited_urls))
            print("Loaded {} entries".format(len(visited_urls)))
            

        print("Finished loading state ...")



async def run():
    base_url = "https://www.acronis.com/en-us/" 
    async with async_playwright() as playwright_instance:
    
        cookies = "isGpcEnabled=1&datestamp=Mon+Nov+14+2022+14:25:31+GMT-0600+(Central+Standard+Time)&version=6.24.0&isIABGlobal=false&hosts=&consentId=b74a33ec-8baa-431e-a80a-c005cac6e797&interactionCount=1&landingPath=NotLandingPage&groups=C0001:1,C0002:1,C0003:1,C0004:0&AwaitingReconsent=false"

        cookies = "visitor_id=4cb87349-9443-4912-b73e-d631c05d91ce; new_language=es; isAnalyticEventsLimit=true; steamid=76561198080688709; avatar=https://avatars.akamai.steamstatic.com/3b43a3611b8bd0b3a97af4d7a396afe088ddfe7b_medium.jpg; username=Tlue%20Talloon; registered_user=true; AB_TEST_SWAP_SKIN_CARDS_LOGIC_PROD_329=a"






        base_url = "https://www.acronis.com/en-us/" 

        spider = WebSpider(base_url, playwright_instance, headless=False, cookies=cookies)

        spider.load_state(visited_urls="./sites.txt", additional_start_domains="/home/kai/Projects/bug-bounty/acronis.com/recon.txt")
        #spider.load_state(visited_urls=None, additional_start_domains="/home/kai/Projects/bug-bounty/acronis.com/recon.txt")
        
        handler =  UrlHandler(base_url,
                         allowed_domains=[" .*.acronis.*"],
                         allowed_paths=[], 
                         disallowed_paths=[
                                        "/es-mx/",
                                        "/bg-bg/", 
                                        "/cs-cz/",
                                        "/de-de/",
                                        "/en-au/",
                                        "/en-eu/",
                                        "/en-hk/",
                                        "/en-in/",
                                        "/en-sg/",
                                        "/en-gb/",
                                        "/es-es/",
                                        "/fr-ca/",
                                        "/fr-fr/",
                                        "/id-id/",
                                        "/it-it/",
                                        "/ja-jp/",
                                        "/ko-kr/",
                                        "/pl-pl/",
                                        "/pt-br/",
                                        "/pt-pt/",
                                        "/ro-ro/",
                                        "/ru-ru/",
                                        "/tr-tr/",
                                        "/zh-cn/",
                                        "/zh-tw/",
                                        "/content/",
                                        "/resource-center/",
                                        "/blog/"
                         ], 
                         allowed_params=[], 
                         allowed_queries=[], 
                         allowed_fragments=[])

        spider.set_url_handler(handler)

        unique_urls = await spider.crawl()


        print(unique_urls)
        


if __name__ == "__main__":
    asyncio.run(run())





