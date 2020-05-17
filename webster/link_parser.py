import abc
from typing import List, Set
from urllib.parse import urlparse, urljoin, urldefrag

from typing_extensions import Protocol

from webster.response import Response
from lxml import html as lh


class AbstractLinkParser(Protocol):

    def __init__(self, allowed_domains: List[str]):
        self.allowed_domains = allowed_domains

    @abc.abstractmethod
    def parse_links(self, response: Response) -> Set[str]:
        pass


class DefaultParser:

    def __init__(self, allowed_domains: List[str]):
        self.allowed_domains = allowed_domains

    def parse_links(self, response: Response) -> Set[str]:
        allowed_domains = [urlparse(u).netloc for u in self.allowed_domains]
        dom = lh.fromstring(response.html)
        links = dom.cssselect('a[href]')
        found = set()
        for link in links:
            try:
                base = urljoin(response.url, link.get('href'))
                net_location = urlparse(base).netloc
                if net_location in allowed_domains:
                    cleaned, _ = urldefrag(base)
                    found.add(cleaned)
            except ValueError:
                continue
        return found

