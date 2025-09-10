from collections.abc import Sequence
from typing import Any, overload

from langchain_cohere import CohereRerank
from langchain_core.callbacks.base import Callbacks
from langchain_core.documents.base import Document
from langchain_core.documents.compressor import BaseDocumentCompressor
from pydantic import BaseModel


class RankResult(BaseModel): ...


class LlmBaseRerank(BaseDocumentCompressor):
    def rerank(
        self,
        documents: Sequence[str | Document | dict[str, Any]],
        query: str,
        *,
        rank_fields: Sequence[str] | None = None,
        top_n: int | None = -1,
    ) -> list[RankResult]: ...

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Callbacks | None = None,
    ) -> Sequence[Document]: ...


@overload
def rerank_factory(): ...
@overload
def rerank_factory(maxsize: int, ttl: float): ...
@overload
def rerank_factory(cache: Any): ...
def rerank_factory(
    maxsize: int | None = 10, ttl: float | None = 360, cache: Any | None = None
):
    def factory(model: str, base_url: str, api_key: str, **kwargs: Any):
        if "rerank" in model:
            return CohereRerank(
                base_url=base_url, model=model, cohere_api_key=api_key, **kwargs
            )
        else:
            return LlmBaseRerank(
                model=model, base_url=base_url, api_key=api_key, **kwargs
            )

    return factory
