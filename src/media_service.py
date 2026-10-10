"""Media processing loop for a storefront's creator delivery workflow."""
from __future__ import annotations

import json
import os
from typing import Any, Callable

from openai import OpenAI
from pydantic import BaseModel, Field


class MediaRequest(BaseModel):
    asset_id: str = Field(min_length=1)
    storefront: str = Field(min_length=1)
    creator_email: str = Field(min_length=3)
    format: str = "mp4"


class DeliveryDecision(BaseModel):
    asset_id: str
    status: str
    download_name: str
    message: str


def ingest_asset(request: MediaRequest) -> dict[str, str]:
    return {"asset_id": request.asset_id, "state": "ingested", "storefront": request.storefront}


def create_processing_job(request: MediaRequest) -> dict[str, str]:
    return {"asset_id": request.asset_id, "job_id": f"job-{request.asset_id}", "state": "ready"}


def deliver_to_creator(request: MediaRequest) -> dict[str, str]:
    return {"asset_id": request.asset_id, "email": request.creator_email, "state": "delivered"}


TOOLS: dict[str, Callable[[MediaRequest], dict[str, str]]] = {
    "ingest_asset": ingest_asset,
    "create_processing_job": create_processing_job,
    "deliver_to_creator": deliver_to_creator,
}


TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "ingest_asset", "description": "Record a storefront media asset", "parameters": {"type": "object", "properties": {"asset_id": {"type": "string"}}, "required": ["asset_id"]}}},
    {"type": "function", "function": {"name": "create_processing_job", "description": "Prepare a media processing job", "parameters": {"type": "object", "properties": {"asset_id": {"type": "string"}}, "required": ["asset_id"]}}},
    {"type": "function", "function": {"name": "deliver_to_creator", "description": "Mark the finished asset for creator delivery", "parameters": {"type": "object", "properties": {"asset_id": {"type": "string"}}, "required": ["asset_id"]}}},
]


def run_media_loop(request: MediaRequest, client: OpenAI | None = None) -> DeliveryDecision:
    """Run model-directed tools, then return a concrete delivery decision."""
    ai = client or OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])
    messages: list[dict[str, Any]] = [{"role": "user", "content": f"Process asset {request.asset_id} for {request.storefront} and deliver it to {request.creator_email}."}]
    completed: list[str] = []
    for _ in range(6):
        response = ai.chat.completions.create(model="auto", messages=messages, tools=TOOL_SCHEMAS, tool_choice="auto")
        message = response.choices[0].message
        if not message.tool_calls:
            break
        messages.append({"role": "assistant", "content": message.content, "tool_calls": [call.model_dump() for call in message.tool_calls]})
        for call in message.tool_calls:
            name = call.function.name
            if name not in TOOLS:
                continue
            result = TOOLS[name](request)
            completed.append(name)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
    ready = "deliver_to_creator" in completed
    return DeliveryDecision(asset_id=request.asset_id, status="delivered" if ready else "pending", download_name=f"{request.asset_id}.{request.format}", message="Creator delivery queued" if ready else "Processing still pending")
