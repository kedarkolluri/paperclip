"""CLI entry point using Click."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version="0.2.7", prog_name="paperclip")
def cli() -> None:
    """Paperclip AI Agent Management Platform."""
    pass


# --- Run Server ---

@cli.command()
@click.option("--host", default=None, help="Bind host")
@click.option("--port", default=None, type=int, help="Bind port")
@click.option("--log-level", default=None, help="Log level")
def run(host: str | None, port: int | None, log_level: str | None) -> None:
    """Start the Paperclip server."""
    import uvicorn
    from app.config import AppConfig

    config = AppConfig.load()
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=host or config.host,
        port=port or config.port,
        log_level=log_level or config.log_level,
        reload=False,
    )


# --- Dev Server (with reload) ---

@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=3100, type=int)
def dev(host: str, port: int) -> None:
    """Start the server in development mode with auto-reload."""
    import uvicorn
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=host,
        port=port,
        reload=True,
        log_level="debug",
    )


# --- Doctor ---

@cli.command()
def doctor() -> None:
    """Run diagnostic checks."""
    console.print("[bold]Paperclip Doctor[/bold]\n")

    checks = [
        ("Python version", _check_python),
        ("Config file", _check_config),
        ("Database connectivity", _check_db),
        ("Storage", _check_storage),
    ]

    all_ok = True
    for name, fn in checks:
        try:
            ok, msg = fn()
            status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
            if not ok:
                all_ok = False
        except Exception as exc:
            status = "[red]ERROR[/red]"
            msg = str(exc)
            all_ok = False
        console.print(f"  {status}  {name}: {msg}")

    if all_ok:
        console.print("\n[green]All checks passed![/green]")
    else:
        console.print("\n[yellow]Some checks failed. See above.[/yellow]")
        sys.exit(1)


def _check_python() -> tuple[bool, str]:
    v = sys.version_info
    ok = v >= (3, 11)
    return ok, f"{v.major}.{v.minor}.{v.micro}" + ("" if ok else " (requires >=3.11)")


def _check_config() -> tuple[bool, str]:
    config_path = Path.home() / ".paperclip" / "config.json"
    if config_path.exists():
        return True, str(config_path)
    return True, "Using defaults (no config file)"


def _check_db() -> tuple[bool, str]:
    from app.config import AppConfig
    config = AppConfig.load()
    return True, config.db.effective_url.split("@")[-1] if "@" in config.db.effective_url else "embedded"


def _check_storage() -> tuple[bool, str]:
    from app.config import AppConfig
    config = AppConfig.load()
    return True, f"{config.storage.provider}"


# --- Configure ---

@cli.command()
@click.argument("key")
@click.argument("value")
def configure(key: str, value: str) -> None:
    """Set a configuration value."""
    config_path = Path.home() / ".paperclip" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if config_path.exists():
        data = json.loads(config_path.read_text())
    data[key] = value
    config_path.write_text(json.dumps(data, indent=2))
    console.print(f"Set [bold]{key}[/bold] = {value}")


# --- DB Migrate ---

@cli.command("db-migrate")
def db_migrate() -> None:
    """Run database migrations."""
    console.print("Running migrations...")
    asyncio.run(_run_migrations())
    console.print("[green]Migrations complete.[/green]")


async def _run_migrations() -> None:
    from app.config import AppConfig
    from app.database import init_db
    from app.models import Base
    from sqlalchemy.ext.asyncio import create_async_engine

    config = AppConfig.load()
    engine = create_async_engine(config.db.effective_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


# --- Company CLI ---

@cli.group()
def company() -> None:
    """Manage companies."""
    pass


@company.command("list")
@click.option("--server", default="http://localhost:3100", help="Server URL")
def company_list(server: str) -> None:
    """List all companies."""
    import httpx
    resp = httpx.get(f"{server}/api/companies")
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code}[/red]")
        return
    companies = resp.json()
    table = Table(title="Companies")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Prefix")
    table.add_column("Status")
    for c in companies:
        table.add_row(c["id"][:8], c["name"], c["issue_prefix"], c["status"])
    console.print(table)


# --- Agent CLI ---

@cli.group()
def agent() -> None:
    """Manage agents."""
    pass


@agent.command("list")
@click.argument("company_id")
@click.option("--server", default="http://localhost:3100")
def agent_list(company_id: str, server: str) -> None:
    """List agents in a company."""
    import httpx
    resp = httpx.get(f"{server}/api/companies/{company_id}/agents")
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code}[/red]")
        return
    agents = resp.json()
    table = Table(title="Agents")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Adapter")
    for a in agents:
        table.add_row(a["id"][:8], a["name"], a["role"], a["status"], a["adapter_type"])
    console.print(table)


@agent.command("wakeup")
@click.argument("agent_id")
@click.option("--server", default="http://localhost:3100")
@click.option("--reason", default=None)
def agent_wakeup(agent_id: str, server: str, reason: str | None) -> None:
    """Wake up an agent."""
    import httpx
    body = {"source": "cli"}
    if reason:
        body["reason"] = reason
    resp = httpx.post(f"{server}/api/agents/{agent_id}/wakeup", json=body)
    if resp.status_code == 200:
        console.print("[green]Wakeup request sent.[/green]")
    else:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")


# --- Issue CLI ---

@cli.group()
def issue() -> None:
    """Manage issues."""
    pass


@issue.command("list")
@click.argument("company_id")
@click.option("--server", default="http://localhost:3100")
@click.option("--status", default=None)
def issue_list(company_id: str, server: str, status: str | None) -> None:
    """List issues in a company."""
    import httpx
    params = {}
    if status:
        params["status"] = status
    resp = httpx.get(f"{server}/api/companies/{company_id}/issues", params=params)
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code}[/red]")
        return
    issues = resp.json()
    table = Table(title="Issues")
    table.add_column("ID")
    table.add_column("Identifier")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Priority")
    for i in issues:
        table.add_row(
            i["id"][:8], i.get("identifier", ""), i["title"][:50],
            i["status"], i["priority"],
        )
    console.print(table)


@issue.command("create")
@click.argument("company_id")
@click.argument("title")
@click.option("--server", default="http://localhost:3100")
@click.option("--description", default=None)
@click.option("--priority", default="medium")
def issue_create(
    company_id: str, title: str, server: str,
    description: str | None, priority: str,
) -> None:
    """Create a new issue."""
    import httpx
    body = {"title": title, "priority": priority}
    if description:
        body["description"] = description
    resp = httpx.post(f"{server}/api/companies/{company_id}/issues", json=body)
    if resp.status_code == 201:
        data = resp.json()
        console.print(f"[green]Created issue {data.get('identifier', data['id'][:8])}[/green]")
    else:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")


# --- Dashboard CLI ---

@cli.command("dashboard")
@click.argument("company_id")
@click.option("--server", default="http://localhost:3100")
def dashboard(company_id: str, server: str) -> None:
    """Show dashboard for a company."""
    import httpx
    resp = httpx.get(f"{server}/api/companies/{company_id}/dashboard")
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code}[/red]")
        return
    data = resp.json()
    console.print(f"\n[bold]Dashboard for {company_id[:8]}[/bold]\n")
    console.print(f"  Agents:    {json.dumps(data.get('agents', {}))}")
    console.print(f"  Issues:    {json.dumps(data.get('issues', {}))}")
    console.print(f"  Budget:    {data.get('budget_monthly_cents', 0)} cents/month")
    console.print(f"  Spent:     {data.get('cost_monthly_cents', 0)} cents/month")
    console.print(f"  Pending:   {data.get('pending_approvals', 0)} approvals")
    console.print(f"  Stale:     {data.get('stale_tasks', 0)} tasks")


# --- Auth Bootstrap ---

@cli.group()
def auth() -> None:
    """Authentication management."""
    pass


@auth.command("bootstrap-ceo")
@click.option("--server", default="http://localhost:3100")
def bootstrap_ceo(server: str) -> None:
    """Generate the first admin invite URL."""
    import secrets
    token = secrets.token_urlsafe(32)
    console.print(f"\n[bold]Bootstrap invite URL:[/bold]")
    console.print(f"  {server}/invite/{token}")
    console.print(f"\n  Token: {token}")
    console.print("\n[yellow]Note: Use this URL to create the first admin account.[/yellow]")


if __name__ == "__main__":
    cli()
