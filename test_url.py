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


async def run():
    base_url = "https://cs.money/" 
    async with async_playwright() as playwright_instance:
"_schn=_gilil5; _scid=2eb22678-58ca-4cd8-933e-2ea7f2ef17a2; _sctr=1|1668751200000; visitor_id=4cb87349-9443-4912-b73e-d631c05d91ce;  new_language=es;  isAnalyticEventsLimit=true;  steamid=76561198080688709;  avatar=https://avatars.akamai.steamstatic.com/3b43a3611b8bd0b3a97af4d7a396afe088ddfe7b_medium.jpg;  username=Tlue%20Talloon;  registered_user=true;  AB_TEST_SWAP_SKIN_CARDS_LOGIC_PROD_329=a; new_language=es; AB_TEST_SWAP_SKIN_CARDS_LOGIC_PROD_329=a; amplitude_id_c14fa5162b6e034d1c3b12854f3a26f5cs.money=eyJkZXZpY2VJZCI6Ijg3NGZjZDMwLWRhZTAtNGU2Ny04YTE5LTk0YWE0MmVhZTM3MVIiLCJ1c2VySWQiOm51bGwsIm9wdE91dCI6ZmFsc2UsInNlc3Npb25JZCI6MTY2ODgyMDc1NTA2NCwibGFzdEV2ZW50VGltZSI6MTY2ODgyMDc1NTA2NywiZXZlbnRJZCI6MSwiaWRlbnRpZnlJZCI6Mywic2VxdWVuY2VOdW1iZXIiOjR9; sc=0C59105A-57FD-AF5F-5BF5-70797051568E; _gcl_au=1.1.1253103214.1668820756; _ga_HY7CCPCD7H=GS1.1.1668820757.1.0.1668820757.60.0.0; _dc_gtm_UA-77178353-1=1; _hjSessionUser_2848248=eyJpZCI6IjA5MDg5ZTgwLTE1YmYtNTM1MC1iNzc3LTU0MzdlMWU3MzVjMCIsImNyZWF0ZWQiOjE2Njg4MjA3NTYxNzAsImV4aXN0aW5nIjpmYWxzZX0=; _hjFirstSeen=1; _hjIncludedInSessionSample=1; _hjSession_2848248=eyJpZCI6ImU2ZThmMGMzLTEzOGYtNGE4NC04YWRmLTU3NzMxY2RmMTJjMSIsImNyZWF0ZWQiOjE2Njg4MjA3NTcyNjgsImluU2FtcGxlIjp0cnVlfQ==; _hjIncludedInPageviewSample=1; _hjAbsoluteSessionInProgress=0; _hjCachedUserAttributes=eyJhdHRyaWJ1dGVzIjp7fSwidXNlcklkIjoiNzY1NjExOTgwODA2ODg3MDkifQ==; _uetsid=2ffc73c067a811ed9b9c85a9f2ac776e; _uetvid=2ffc742067a811ed89503f39374b7392; _ym_uid=16688207591034271624; _ym_d=1668820759; _ym_isad=2; _ym_visorc=b; _fbp=fb.1.1668820757230.758778302; _ga=GA1.2.765755382.1668820757; _gid=GA1.2.1662065185.1668820757"     


        cookies = "visitor_id=4cb87349-9443-4912-b73e-d631c05d91ce; new_language=es; isAnalyticEventsLimit=true; steamid=76561198080688709; avatar=https://avatars.akamai.steamstatic.com/3b43a3611b8bd0b3a97af4d7a396afe088ddfe7b_medium.jpg; username=Tlue%20Talloon; registered_user=true; AB_TEST_SWAP_SKIN_CARDS_LOGIC_PROD_329=a"

'visitor_id=4cb87349-9443-4912-b73e-d631c05d91ce; new_language=es; isAnalyticEventsLimit=true; registered_user=true; AB_TEST_SWAP_SKIN_CARDS_LOGIC_PROD_329=a; steamid=76561198080688709; avatar=https://avatars.akamai.steamstatic.com/3b43a3611b8bd0b3a97af4d7a396afe088ddfe7b_medium.jpg; username=Tlue%20Talloon'


        page_handler = PageHandler(playwright_instance, cookies=cookies, headless=False, debug=False)


        await page_handler.load_page(base_url, block=False)
        time.sleep(1000)

if __name__ == "__main__":
    asyncio.run(run())

