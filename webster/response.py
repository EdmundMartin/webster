class Response:

    __slots__ = ["url", "requested_url", "html", "status", "headers"]

    def __init__(self, requested_url: str, page_content: str, response):
        self.url = response.url
        self.requested_url = requested_url
        self.html = page_content
        self.status = response.status
        self.headers = response.headers

    @property
    def status_ok(self) -> bool:
        return self.status < 300

    @property
    def is_redirect(self) -> bool:
        return self.requested_url != self.url

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise Exception("Did not receive a 2XX Code")

    def __repr__(self):
        return "Response(url={}, status_code={})".format(self.url, self.status)
