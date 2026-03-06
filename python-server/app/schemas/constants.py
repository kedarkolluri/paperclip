"""Shared constants mirroring @paperclipai/shared/constants."""

from __future__ import annotations

# Company statuses
COMPANY_STATUSES = ("active", "paused", "archived")

# Agent statuses
AGENT_STATUSES = (
    "active",
    "paused",
    "idle",
    "running",
    "error",
    "pending_approval",
    "terminated",
)

# Agent adapter types
AGENT_ADAPTER_TYPES = (
    "process",
    "http",
    "claude_local",
    "codex_local",
    "opencode_local",
    "cursor",
    "openclaw",
)

# Agent roles
AGENT_ROLES = (
    "general",
    "manager",
    "specialist",
    "intern",
    "contractor",
    "executive",
)

# Issue statuses
ISSUE_STATUSES = (
    "backlog",
    "open",
    "in_progress",
    "blocked",
    "in_review",
    "done",
    "cancelled",
)

# Issue priorities
ISSUE_PRIORITIES = ("critical", "high", "medium", "low", "none")

# Approval statuses
APPROVAL_STATUSES = ("pending", "approved", "rejected", "revision_requested")

# Approval types
APPROVAL_TYPES = (
    "hire_agent",
    "budget_increase",
    "general",
    "tool_use",
    "code_review",
)

# Goal levels
GOAL_LEVELS = ("vision", "strategy", "objective", "key_result", "task")

# Goal statuses
GOAL_STATUSES = ("planned", "active", "completed", "cancelled")

# Project statuses
PROJECT_STATUSES = ("backlog", "active", "completed", "archived")

# Deployment modes
DEPLOYMENT_MODES = ("local_trusted", "authenticated")

# Deployment exposures
DEPLOYMENT_EXPOSURES = ("private", "public")

# Heartbeat run statuses
RUN_STATUSES = ("queued", "running", "completed", "failed", "cancelled", "timed_out")

# Wakeup request statuses
WAKEUP_STATUSES = ("queued", "claimed", "completed", "failed", "coalesced")

# Activity actor types
ACTOR_TYPES = ("system", "agent", "user", "board")

# Invite types
INVITE_TYPES = ("company_join", "bootstrap_ceo")

# Join request types
JOIN_REQUEST_TYPES = ("agent", "user")

# Join request statuses
JOIN_REQUEST_STATUSES = ("pending_approval", "approved", "rejected")

# Secret providers
SECRET_PROVIDERS = ("local_encrypted", "aws_sm", "gcp_sm", "vault")

# Storage providers
STORAGE_PROVIDERS = ("local_disk", "s3")

# Allowed image content types for uploads
ALLOWED_IMAGE_TYPES = frozenset({
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
})
