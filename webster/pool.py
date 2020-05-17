import asyncio

from pyppeteer import launch
from pyppeteer.page import Page


class BrowserPool:
    def __init__(self):
        self._browser = None
        self._page_queue: asyncio.Queue = asyncio.Queue()
        self.size = 0

    @classmethod
    async def create_browser_pool(
        cls, tab_count: int, headless: bool = False
    ) -> "BrowserPool":
        klass = cls()
        klass._browser = await launch(headless=headless)
        for i in range(tab_count):
            page = await klass._browser.newPage()
            await klass._page_queue.put(page)
        klass.size = tab_count
        return klass

    async def add_page(self, page) -> None:
        await self._page_queue.put(page)

    async def acquire_page(self) -> Page:
        return await self._page_queue.get()


if __name__ == "__main__":
    asyncio.run(BrowserPool.create_browser_pool(5))
