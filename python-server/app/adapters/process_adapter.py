"""Process adapter – runs local commands."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any

from app.adapters.base import (
    AdapterExecuteInput,
    AdapterExecuteResult,
    AdapterTestResult,
    BaseAdapter,
)


class ProcessAdapter(BaseAdapter):
    adapter_type = "process"

    async def execute(self, input: AdapterExecuteInput) -> AdapterExecuteResult:
        cmd = input.adapter_config.get("command", "")
        args = input.adapter_config.get("args", [])
        cwd = input.adapter_config.get("cwd")
        timeout = input.runtime_config.get("timeout_seconds", 300)

        if not cmd:
            return AdapterExecuteResult(
                exit_code=1,
                error="No command configured",
                error_code="no_command",
            )

        env = {**os.environ, **input.env_vars}
        if input.jwt_token:
            env["PAPERCLIP_AGENT_TOKEN"] = input.jwt_token
        env["PAPERCLIP_AGENT_ID"] = str(input.agent_id)
        env["PAPERCLIP_COMPANY_ID"] = str(input.company_id)
        env["PAPERCLIP_RUN_ID"] = str(input.run_id)

        full_cmd = [cmd] + args

        try:
            proc = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            stdout = stdout_bytes.decode(errors="replace")
            stderr = stderr_bytes.decode(errors="replace")

            return AdapterExecuteResult(
                exit_code=proc.returncode or 0,
                stdout_excerpt=stdout[:10000] if stdout else None,
                stderr_excerpt=stderr[:10000] if stderr else None,
                error=stderr[:2000] if proc.returncode != 0 and stderr else None,
            )
        except asyncio.TimeoutError:
            return AdapterExecuteResult(
                exit_code=-1,
                error=f"Process timed out after {timeout}s",
                error_code="timeout",
            )
        except FileNotFoundError:
            return AdapterExecuteResult(
                exit_code=-1,
                error=f"Command not found: {cmd}",
                error_code="command_not_found",
            )
        except Exception as exc:
            return AdapterExecuteResult(
                exit_code=-1,
                error=str(exc),
                error_code="execution_error",
            )

    async def test(self, adapter_config: dict, runtime_config: dict) -> AdapterTestResult:
        cmd = adapter_config.get("command", "")
        if not cmd:
            return AdapterTestResult(success=False, message="No command configured")
        import shutil
        if not shutil.which(cmd):
            return AdapterTestResult(success=False, message=f"Command '{cmd}' not found in PATH")
        return AdapterTestResult(success=True, message=f"Command '{cmd}' is available")
