# Webster

Webster is a minimal crawling framework built on top of pyppeteer. It allows for the easy creation of web crawlers 
which have the ability to async render pages. It also allows users to define custom link parsing and parsing logic ontop of 
the behaviour of the base crawler. Webster maintains a pool of browser tabs allowing one Chromium instance to make 
multiple requests in parallel.

Webster is still relatively light in regards to features but provides a functional interface for crawling the web 
backed 

# Simple Example 
```python
import asyncio
from webster.crawler import WebsterCrawler

async def test():
    crawler = await WebsterCrawler.new_crawler("https://www.dailymail.co.uk/home/index.html", ["https://www.dailymail.co.uk/home/index.html"], 3)
    await crawler.crawl()

asyncio.run(test())
```

## Saving Results
To save results, it is necessary to implement your own saver class and pass into a crawler as such:
```python
import asyncio
from webster.crawler import WebsterCrawler
from webster.response import Response

class MySaver:
    
    async def save_result(self, response: Response):
        print(response.url)
        print(response.html)
        #TODO parse HTML and save results

async def test():
    saver = MySaver()
    crawler = await WebsterCrawler.new_crawler("http://example.com", ["https://example.com"], 3, saver=saver)
    await crawler.crawl()

asyncio.run(test())
```
The above example simple prints the URL and the HTML returned. But it would be here that a more robust saver could 
implemented parsing the HTML and saving the results to some form of data storage. The default saver simply passes by
visited pages.

## Custom Crawling rules
Should you want to implement custom rules regarding which pages should and should not be visited. Overriding the 
default behaviour of the crawler to visit any pages within the allowed domains list, you can simply implement a simply 
link parser class. An example of such can be found below:
```python
import asyncio
from typing import Set

from lxml import html as lh
from urllib.parse import urljoin, urlparse, urldefrag

from webster.crawler import WebsterCrawler
from webster.response import Response


class PythonParser:

    def parse_links(self, response: Response) -> Set[str]:
        allowed_languages = ['javascript', 'python', 'java']
        dom = lh.fromstring(response.html)
        links = dom.cssselect('a[href]')
        found = set()
        for link in links:
            try:
                base = urljoin(response.url, link.get('href'))
                if any([i in base for i in allowed_languages]):
                    cleaned, _ = urldefrag(base)
                    found.add(cleaned)
            except ValueError:
                continue
        return found

async def test():
    parser = PythonParser()
    crawler = await WebsterCrawler.new_crawler("http://example.com", ["https://example.com"], 3, link_parser=parser)
    await crawler.crawl()

asyncio.run(test())
```