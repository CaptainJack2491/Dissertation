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
    import openai
except ImportError:
    openai = None

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
    usage: Optional[Dict[str, int]] = None
    latency_ms: Optional[int] = None
    model: Optional[str] = None


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


class OpenAIBatchProvider(BatchProvider):
    def __init__(self, api_key: Optional[str] = None):
        if openai is None:
            raise ImportError("openai not installed. Run: uv add openai")
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        self.client = openai.OpenAI(api_key=key)

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
        openai_requests = [
            {
                "custom_id": r.custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": r.params["model"],
                    "max_tokens": r.params["max_tokens"],
                    "temperature": r.params["temperature"],
                    "messages": r.params["messages"],
                },
            }
            for r in requests
        ]
        response = self.client.batches.create(
            input_file_id=self._upload_requests(openai_requests),
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        return response.id

    def _upload_requests(self, requests: List[Dict]) -> str:
        import json

        content = "\n".join(json.dumps(req) for req in requests)
        import io

        file_obj = io.BytesIO(content.encode("utf-8"))
        upload = self.client.files.create(file=file_obj, purpose="batch")
        return upload.id

    def poll_batch(self, batch_id: str, poll_interval: int = 30) -> None:
        while True:
            batch = self.client.batches.retrieve(batch_id)
            status = batch.status
            counts = batch.request_counts
            print(
                f"  Batch {batch_id}: {status} "
                f"(completed={counts.completed}, "
                f"failed={counts.failed}, "
                f"total={counts.total})"
            )
            if status in ["completed", "failed", "expired"]:
                return
            time.sleep(poll_interval)

    def collect_results(self, batch_id: str) -> Iterator[BatchResult]:
        batch = self.client.batches.retrieve(batch_id)
        if not batch.output_file_id:
            return

        response = self.client.files.content(batch.output_file_id)
        import json

        for line in response.text.strip().split("\n"):
            if not line:
                continue
            data = json.loads(line)
            custom_id = data.get("custom_id", "")
            if data.get("error"):
                yield BatchResult(
                    custom_id=custom_id,
                    text="",
                    error=data["error"].get("message", "Unknown error"),
                )
            else:
                body = data["response"]["body"]
                msg = body["choices"][0]["message"]
                text = msg.get("content", "")
                usage = body.get("usage", {})
                yield BatchResult(
                    custom_id=custom_id,
                    text=text,
                    usage=usage,
                    model=body.get("model", ""),
                )
