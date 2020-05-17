from typing_extensions import Protocol

from webster.response import Response


class Saver(Protocol):

    async def save_result(self, response: Response) -> None:
        pass


class NullSaver:
    async def save_result(self, response: Response) -> None:
        return None