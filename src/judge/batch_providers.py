"""
Batch providers for the judge system.
Supports Anthropic and xAI batch APIs.
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

import anthropic

try:
    from xai_sdk import Client as XAIClient
except ImportError:
    XAIClient = None

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class BatchRequest:
    custom_id: str
    params: Dict[str, Any]


@dataclass
class BatchResult:
    custom_id: str
    text: str
    error: Optional[str] = None


class BatchProvider(ABC):
    @abstractmethod
    def submit_batch(self, requests: List[BatchRequest]) -> str:
        pass

    @abstractmethod
    def poll_batch(self, batch_id: str, poll_interval: int = 30) -> None:
        pass

    @abstractmethod
    def collect_results(self, batch_id: str) -> Iterator[BatchResult]:
        pass

    @abstractmethod
    def build_request(
        self,
        custom_id: str,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int = 4096,
    ) -> BatchRequest:
        pass


class AnthropicBatchProvider(BatchProvider):
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=key)

    def build_request(
        self,
        custom_id: str,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int = 4096,
    ) -> BatchRequest:
        return BatchRequest(
            custom_id=custom_id,
            params={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

    def submit_batch(self, requests: List[BatchRequest]) -> str:
        anthropic_requests = [
            {
                "custom_id": r.custom_id,
                "params": r.params,
            }
            for r in requests
        ]
        response = self.client.messages.batches.create(requests=anthropic_requests)
        return response.id

    def poll_batch(self, batch_id: str, poll_interval: int = 30) -> None:
        while True:
            batch = self.client.messages.batches.retrieve(batch_id)
            status = batch.processing_status
            counts = batch.request_counts
            print(
                f"  Batch {batch_id}: {status} "
                f"(succeeded={counts.succeeded}, "
                f"processing={counts.processing}, "
                f"errored={counts.errored})"
            )
            if status == "ended":
                return
            time.sleep(poll_interval)

    def collect_results(self, batch_id: str) -> Iterator[BatchResult]:
        for result in self.client.messages.batches.results(batch_id):
            custom_id = result.custom_id
            if result.result.type == "succeeded":
                content = result.result.message.content
                if hasattr(content, "__iter__") and not isinstance(content, str):
                    for block in content:
                        if hasattr(block, "text"):
                            text = block.text
                            break
                    else:
                        text = ""
                else:
                    text = str(content)
                yield BatchResult(custom_id=custom_id, text=text)
            else:
                yield BatchResult(
                    custom_id=custom_id, text="", error=f"ERROR: {result.result.type}"
                )


class XAIBatchProvider(BatchProvider):
    def __init__(self, api_key: Optional[str] = None):
        if XAIClient is None:
            raise ImportError("xai-sdk not installed. Run: uv add xai-sdk")
        key = api_key or os.environ.get("XAI_API_KEY")
        if not key:
            raise ValueError("XAI_API_KEY not set")
        self.client = XAIClient(api_key=key)

    def build_request(
        self,
        custom_id: str,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int = 4096,
    ) -> BatchRequest:
        return BatchRequest(
            custom_id=custom_id,
            params={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            },
        )

    def submit_batch(self, requests: List[BatchRequest]) -> str:
        from xai_sdk.chat import system as xai_system, user as xai_user

        batch = self.client.batch.create(batch_name=f"judge_batch_{int(time.time())}")
        batch_requests = []
        for req in requests:
            chat = self.client.chat.create(
                model=req.params["model"],
                batch_request_id=req.custom_id,
            )
            for msg in req.params["messages"]:
                if msg["role"] == "system":
                    chat.append(xai_system(msg["content"]))
                else:
                    chat.append(xai_user(msg["content"]))
            batch_requests.append(chat)
        self.client.batch.add(batch_id=batch.batch_id, batch_requests=batch_requests)
        return batch.batch_id

    def poll_batch(self, batch_id: str, poll_interval: int = 30) -> None:
        while True:
            batch = self.client.batch.get(batch_id=batch_id)
            state = batch.state
            print(
                f"  Batch {batch_id}: "
                f"(pending={state.num_pending}, "
                f"success={state.num_success}, "
                f"error={state.num_error})"
            )
            if state.num_pending == 0:
                return
            time.sleep(poll_interval)

    def collect_results(self, batch_id: str) -> Iterator[BatchResult]:
        pagination_token = None
        while True:
            page = self.client.batch.list_batch_results(
                batch_id=batch_id,
                limit=100,
                pagination_token=pagination_token,
            )
            for result in page.succeeded:
                rid = result.batch_request_id
                text = result.response.content
                yield BatchResult(custom_id=rid, text=text)
            for result in page.failed:
                yield BatchResult(
                    custom_id=result.batch_request_id,
                    text="",
                    error=result.error_message,
                )
            if page.pagination_token is None:
                break
            pagination_token = page.pagination_token
