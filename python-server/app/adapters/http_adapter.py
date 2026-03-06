"""HTTP adapter – calls remote webhooks."""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from app.adapters.base import (
    AdapterExecuteInput,
    AdapterExecuteResult,
    AdapterTestResult,
    BaseAdapter,
)


class HttpAdapter(BaseAdapter):
    adapter_type = "http"

    async def execute(self, input: AdapterExecuteInput) -> AdapterExecuteResult:
        url = input.adapter_config.get("url", "")
        method = input.adapter_config.get("method", "POST").upper()
        headers = dict(input.adapter_config.get("headers", {}))
        timeout = input.runtime_config.get("timeout_seconds", 300)

        if not url:
            return AdapterExecuteResult(
                exit_code=1,
                error="No URL configured",
                error_code="no_url",
            )

        if input.jwt_token:
            headers["Authorization"] = f"Bearer {input.jwt_token}"
        headers.setdefault("Content-Type", "application/json")

        payload = {
            "agent_id": str(input.agent_id),
            "company_id": str(input.company_id),
            "run_id": str(input.run_id),
            "session_id": input.session_id,
            "task_key": input.task_key,
            "context": input.context_snapshot,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.request(method, url, json=payload, headers=headers)
                body = resp.text[:10000]

                if resp.status_code >= 400:
                    return AdapterExecuteResult(
                        exit_code=resp.status_code,
                        error=f"HTTP {resp.status_code}: {body[:2000]}",
                        stderr_excerpt=body,
                    )

                result_json = None
                try:
                    result_json = resp.json()
                except Exception:
                    pass

                return AdapterExecuteResult(
                    exit_code=0,
                    stdout_excerpt=body,
                    result=result_json,
                    session_id_after=result_json.get("session_id") if result_json else None,
                    external_run_id=result_json.get("run_id") if result_json else None,
                )
        except httpx.TimeoutException:
            return AdapterExecuteResult(
                exit_code=-1,
                error=f"HTTP request timed out after {timeout}s",
                error_code="timeout",
            )
        except Exception as exc:
            return AdapterExecuteResult(
                exit_code=-1,
                error=str(exc),
                error_code="http_error",
            )

    async def test(self, adapter_config: dict, runtime_config: dict) -> AdapterTestResult:
        url = adapter_config.get("url", "")
        if not url:
            return AdapterTestResult(success=False, message="No URL configured")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.head(url)
                return AdapterTestResult(
                    success=resp.status_code < 500,
                    message=f"URL responded with status {resp.status_code}",
                )
        except Exception as exc:
            return AdapterTestResult(success=False, message=str(exc))
