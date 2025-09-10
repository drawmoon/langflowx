import os
from typing import Any, Literal

from cachetools import TTLCache, cached

NLP_Provider = Literal["ltp", "hanlp"]


def provider_factotry(maxsize: int = 100, ttl: float = 360):
    cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def _cache_key_generate(
        provider: NLP_Provider, words: list[str], **kwargs: Any
    ) -> str:
        return f"{provider}_{words}"

    def ltp_parser(words: list[str]):
        from ltp import LTP

        client = LTP(os.getenv("NLP", "LTP/small"), local_files_only=True)
        client.add_words(words)

        def parse_func(texts: list[str], tasks: list[str]):
            return client.pipeline(texts, tasks)

        return parse_func

    @cached(cache, key=_cache_key_generate)
    def factotry(provider: NLP_Provider, words: list[str], **kwargs: Any):
        match provider:
            case "ltp":
                return ltp_parser(words=words, **kwargs)
            case "hanlp":
                ...
            case _:
                ...

    return factotry
