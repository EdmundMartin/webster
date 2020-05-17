import asyncio
from typing import Optional, Union, List
from urllib.parse import urlparse

from async_timeout import timeout
from pyppeteer.page import Page

from webster.pool import BrowserPool
from webster.response import Response
from webster.link_parser import AbstractLinkParser, DefaultParser
from webster.saver import Saver, NullSaver


class WebsterCrawler:
    def __init__(
        self,
        start_urls: Union[List, str],
        allowed_domains: List[str],
        link_parser: Optional[AbstractLinkParser] = None,
        saver: Optional[Saver] = None,
        req_timeout: int = 30,
        post_load: int = 0,
    ):
        self._scheduled_urls = set()
        self._url_queue: asyncio.Queue = self.__seed_queue(start_urls)
        self._allowed_domains = self.__parse_allowed_netlocs(allowed_domains)
        self._link_parser = (
            link_parser
            if link_parser
            else DefaultParser(allowed_domains)
        )
        self._saver = saver if saver else NullSaver()
        self._pool: Optional[BrowserPool] = None
        self._timeout = req_timeout
        self._post_load = post_load

    def __seed_queue(self, start_urls) -> asyncio.Queue:
        queue = asyncio.Queue()
        if isinstance(start_urls, str):
            self._scheduled_urls.add(start_urls)
            queue.put_nowait(start_urls)
            return queue
        for item in start_urls:
            self._scheduled_urls.add(item)
            queue.put_nowait(item)
        return queue

    def __parse_allowed_netlocs(self, allowed_domains: List[str]) -> List[str]:
        return [urlparse(u).netloc for u in allowed_domains]

    @classmethod
    async def new_crawler(
        cls,
        start_urls: Union[List, str],
        allowed_domains: List[str],
        concurrency: int,
        headless: bool = True,
        **kwargs
    ):
        klass = WebsterCrawler(start_urls, allowed_domains, **kwargs)
        klass._pool = await BrowserPool.create_browser_pool(concurrency, headless=headless)
        return klass

    async def _await_post_load(self, time: int):
        if time:
            await asyncio.sleep(time)

    async def _request(self, url) -> Response:
        tab: Page = await self._pool.acquire_page()
        try:
            with timeout(self._timeout):
                response = await tab.goto(url)
                await self._await_post_load(self._post_load)
                page_content = await tab.content()
        except Exception as e:
            print('Exception making request', e)
            raise e
        finally:
            await self._pool.add_page(tab)
        return Response(url, page_content, response)

    async def _work(self):
        while True:
            try:
                url = await self._url_queue.get()
                response = await self._request(url)
                links = self._link_parser.parse_links(response)
                await self._saver.save_result(response)
                for l in links:
                    if l not in self._scheduled_urls:
                        self._scheduled_urls.add(l)
                        await self._url_queue.put(l)
            except asyncio.CancelledError as e:
                return
            except Exception as e:
                print(e)
                self._url_queue.task_done()
            else:
                self._url_queue.task_done()

    async def crawl(self):
        loop = asyncio.get_event_loop()
        workers = [
            asyncio.Task(self._work(), loop=loop) for _ in range(self._pool.size)
        ]
        await self._url_queue.join()
        for w in workers:
            w.cancel()
