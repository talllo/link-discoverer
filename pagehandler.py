
from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright
import random
from threading import Lock
from urllib.parse import urlparse, urljoin
from playwright_stealth import stealth_async

class UrlFilter():
    def __init__(self, debug=False):
        self.debug = debug

    def is_valid_url(self, url):
        return True

    def debug_print(self, format_string, param1, param2, param3=None, verbose=True):
        if self.debug and verbose and param3 != None:
            print(format_string.format(param1, param2, param3))
        elif self.debug and verbose:
            print(format_string.format(param1, param2))



class PageHandler():
    def __init__(self, playwright_instance, cookies=None, headless=False, debug=False):
        self.headless = headless
        self.browser_pool = [] 
        self.contexts = []
        self.lock = Lock()
        self.debug = debug
        self.url_filter = UrlFilter(debug)
        self.page_timeout= 80000
        self.playwright_instance = playwright_instance
        self.cookies = cookies 

    def get_random_headers(self):
        referers = ["https://www.google.com/",
                    "https://search.brave.com/",
                    "https://mx.search.yahoo.com/",
                    "https://duckduckgo.com/"]

        extra_http_headers = {
            'Referer': random.choice(referers),
        }



        return extra_http_headers

    def get_random_user_agent(self):
        agent_list_pc = [
            "Mozilla/5.0 (Windows NT 10.0; rv:103.0) Gecko/20100101 Firefox/103.0",
            "Mozilla/5.0 (Windows NT 10.0; rv:103.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/103.0",
        ]
 
        agent = random.choice(agent_list_pc)

        return agent 

    #initialize browser pool with all of our browsers 
    async def init_browser_pool(self):
        self.lock.acquire()
        if len(self.browser_pool) != 0: 
            self.lock.release()
            return
        self.lock.release()

        self.browser_pool = [
                
            await self.playwright_instance.chromium.launch(
                        executable_path = '/snap/bin/brave',
                        headless=self.headless,
                        ignore_default_args=["--mute-audio"],
                        timeout = 30000
                        ),

            await self.playwright_instance.firefox.launch(
                        headless=self.headless,
                        ignore_default_args=["--mute-audio"],
                        timeout = 30000
                        ),
            ]

    #gets a random browser context from out browser pool
    async def get_browser_context(self):
        while True:
            try:
                #choose random browser
                browser = random.choice(self.browser_pool)

                #create new context
                context = await browser.new_context(
                        user_agent = self.get_random_user_agent(),
                        extra_http_headers = self.get_random_headers()
                )

                await context.clear_cookies()
                #init cookies

                cookies_obj = []
                for cookie in self.cookies.split(";"):
                    obj = {
                        "name":  cookie.split("=")[0],
                        "value": "=".join(cookie.split("=")[1:]),
                        "domain": "cs.money",
                        'path': '/'
                    }
                    cookies_obj.append(obj)
                    print(obj)
                    print("\n")
                
                await context.add_cookies(cookies_obj)


                self.lock.acquire()
                self.contexts.append(context)
                self.lock.release)


                return context
            except:

                print(self.get_random_headers())
                print("Failed creating browser context. Retrying ... ")
                continue

    async def clear_browser_context(self, context):
        self.lock.acquire()

        self.contexts.remove(context)


        await context.close()

        self.lock.release()


    async def clear_browser_contexts(self):
        self.lock.acquire()

        for context in self.contexts:
            await context.close()

        self.contexts = []

        self.lock.release()

    ##task that load a page given browser context, and url
    #returns None on error and returns the page on success
    async def load_page_task(self, context, url, should_filter=True):
        if len(self.browser_pool) == 0: 
            self.lock.acquire()
            await self.init_browser_pool()
            self.lock.release()

        if should_filter: 
            if not self.filter.is_valid_url(url): return None

        if url == "" or context == None:
            return None

        self.lock.acquire()
        self.visited_urls.add(url)
        self.lock.release()

        #create new page
        page = await context.new_page()

        await stealth_async(page)
        #go to url and wait until it fully loads

        return await self.load(url, page)

    
    async def load(self, url, page):
        await page.route("**/*", self.page_block)

        #keep retrying page load num_retries times
        for num_retries in range(self.num_retries):
            try: 
                #goto
                await page.goto(url, timeout=TIMEOUT)

                #generate some browser noise to deter bot detection
                #await self.generate_random_browser_noise(page)
                return page

            except Exception as e:
                #print("{}".format(e))
                continue

        return None


    async def load_page(self, url, should_filter = True, block=True):
        await self.init_browser_pool()

        try: 
            #create new browser
            context = await self.get_browser_context()
            
            if context == None: return None
            
            page = await self.load_page_task(context, url, should_filter=should_filter, block=block) 

            return page 
        except:
            print("Failed loading page: " + url)
            return None


    async def load_pages(self, urls, should_filter=True):

        if urls == None: return None

        await self.init_browser_pool()

        #create new browser
        context = await self.get_browser_context()

        #loads a page for each page
        tasks = [self.load_page_task(context, url, should_filter) for url in urls]

        pages = await asyncio.gather(*tasks)

        page_contents = []

        for idx, (page, original_url) in enumerate(zip(pages, urls)):
            if page == None: page_contents.append(None)
            else: 
                try:
                    #handle redirects
                    self.handle_page_redirs(page, original_url, urls, idx)

                    page_contents.append(BeautifulSoup((await page.content()).lower(), "html.parser"))
                except:
                    continue
        
        #close browser context 
        await self.clear_browser_context(context)

        return page_contents

    def handle_page_redirs(self, page, original_url, urls, idx):
        #can do more here if needed

        if original_url == page.url:
            return
        
        urls[idx] = page.url

        #ignores stylesheet, images, and fonts on non facebook pages
    async def page_block(self, route):
        excluded_resource_types = ["stylesheet", "image", "font"]
        if (route.request.resource_type in excluded_resource_types) and not self.debug:
            await route.abort()
        else:
            await route.continue_()

    ##task that load a page given browser context, and url
    #returns None on error and returns the page on success
    async def load_page_task(self, context, url, should_filter=True, block=True):

        if not self.url_filter.is_valid_url(url) and should_filter: return None

        if url == "" or context == None: return None

        #create new page
        page = await context.new_page()

        #apply stealthy protocols
        await stealth_async(page)

        #go to url and wait until it fully loads
        if block:
            await page.route("**/*", self.page_block)

        try:
            await page.goto(url, timeout=self.page_timeout)

            #wait until its elements are visible
            await page.is_visible("html")

            #generate some browser noise to deter bot detection
            await self.generate_random_browser_noise(page)

            return page
        except:
            return None

    async def generate_random_browser_noise(self, page):
        for num_iterations in range(random.randrange(1, 3)):
            #move to left side of page
            await page.mouse.move(random.uniform(75,150),random.uniform(75,150))
        
            await page.mouse.wheel(0, random.uniform(650, 1100))

            await asyncio.sleep(random.uniform(.2,1.5))

            await page.mouse.wheel(0, random.uniform(-500, -350))

