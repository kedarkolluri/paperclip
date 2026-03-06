"""Shared constants mirroring @paperclipai/shared/constants."""

from __future__ import annotations

# Company statuses
COMPANY_STATUSES = ("active", "paused", "archived")

# Deployment modes
DEPLOYMENT_MODES = ("local_trusted", "authenticated")

# Deployment exposures
DEPLOYMENT_EXPOSURES = ("private", "public")

# Auth base URL modes
AUTH_BASE_URL_MODES = ("auto", "explicit")

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
    "ceo",
    "cto",
    "cmo",
    "cfo",
    "engineer",
    "designer",
    "pm",
    "qa",
    "devops",
    "researcher",
    "general",
)

# Agent icon names
AGENT_ICON_NAMES = (
    "bot",
    "cpu",
    "brain",
    "zap",
    "rocket",
    "code",
    "terminal",
    "shield",
    "eye",
    "search",
    "wrench",
    "hammer",
    "lightbulb",
    "sparkles",
    "star",
    "heart",
    "flame",
    "bug",
    "cog",
    "database",
    "globe",
    "lock",
    "mail",
    "message-square",
    "file-code",
    "git-branch",
    "package",
    "puzzle",
    "target",
    "wand",
    "atom",
    "circuit-board",
    "radar",
    "swords",
    "telescope",
    "microscope",
    "crown",
    "gem",
    "hexagon",
    "pentagon",
    "fingerprint",
)

# Issue statuses
ISSUE_STATUSES = (
    "backlog",
    "todo",
    "in_progress",
    "in_review",
    "done",
    "blocked",
    "cancelled",
)

# Issue priorities
ISSUE_PRIORITIES = ("critical", "high", "medium", "low")

# Goal levels
GOAL_LEVELS = ("company", "team", "agent", "task")

# Goal statuses
GOAL_STATUSES = ("planned", "active", "achieved", "cancelled")

# Project statuses
PROJECT_STATUSES = ("backlog", "planned", "in_progress", "completed", "cancelled")

# Project colors
PROJECT_COLORS = (
    "#6366f1",  # indigo
    "#8b5cf6",  # violet
    "#ec4899",  # pink
    "#ef4444",  # red
    "#f97316",  # orange
    "#eab308",  # yellow
    "#22c55e",  # green
    "#14b8a6",  # teal
    "#06b6d4",  # cyan
    "#3b82f6",  # blue
)

# Approval types
APPROVAL_TYPES = ("hire_agent", "approve_ceo_strategy")

# Approval statuses
APPROVAL_STATUSES = ("pending", "revision_requested", "approved", "rejected", "cancelled")

# Secret providers
SECRET_PROVIDERS = ("local_encrypted", "aws_secrets_manager", "gcp_secret_manager", "vault")

# Storage providers
STORAGE_PROVIDERS = ("local_disk", "s3")

# Heartbeat invocation sources
HEARTBEAT_INVOCATION_SOURCES = ("timer", "assignment", "on_demand", "automation")

# Wakeup trigger details
WAKEUP_TRIGGER_DETAILS = ("manual", "ping", "callback", "system")

# Wakeup request statuses
WAKEUP_REQUEST_STATUSES = (
    "queued",
    "deferred_issue_execution",
    "claimed",
    "coalesced",
    "skipped",
    "completed",
    "failed",
    "cancelled",
)

# Heartbeat run statuses
HEARTBEAT_RUN_STATUSES = (
    "queued",
    "running",
    "succeeded",
    "failed",
    "cancelled",
    "timed_out",
)

# Live event types
LIVE_EVENT_TYPES = (
    "heartbeat.run.queued",
    "heartbeat.run.status",
    "heartbeat.run.event",
    "heartbeat.run.log",
    "agent.status",
    "activity.logged",
)

# Principal types
PRINCIPAL_TYPES = ("user", "agent")

# Membership statuses
MEMBERSHIP_STATUSES = ("pending", "active", "suspended")

# Instance user roles
INSTANCE_USER_ROLES = ("instance_admin",)

# Invite types
INVITE_TYPES = ("company_join", "bootstrap_ceo")

# Invite join types
INVITE_JOIN_TYPES = ("human", "agent", "both")

# Join request types
JOIN_REQUEST_TYPES = ("human", "agent")

# Join request statuses
JOIN_REQUEST_STATUSES = ("pending_approval", "approved", "rejected")

# Permission keys
PERMISSION_KEYS = (
    "agents:create",
    "users:invite",
    "users:manage_permissions",
    "tasks:assign",
    "tasks:assign_scope",
    "joins:approve",
)

# Allowed image content types for uploads
ALLOWED_IMAGE_TYPES = frozenset({
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
})
