"""MCP server entrypoint for Domeneshop read tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from .health import HealthDiagnostics
from .sftp_read import SftpReadClient, SftpReadConfig
from . import tools_dry_run, tools_health, tools_read, tools_recovery_plan, tools_sftp_read

mcp = FastMCP("domeneshop-mcp")
api_client = DomeneshopReadClient(DomeneshopConfig.from_env())
remote_client = SftpReadClient(SftpReadConfig.from_env())
health_client = HealthDiagnostics()

@mcp.tool()
def domeneshop_list_domains(domain: str | None = None) -> dict:
    return tools_read.list_domains(api_client, domain=domain)

@mcp.tool()
def domeneshop_get_domain(domain_id: int) -> dict:
    return tools_read.get_domain(api_client, domain_id=domain_id)

@mcp.tool()
def domeneshop_list_dns_records(domain_id: int, host: str | None = None, record_type: str | None = None) -> dict:
    return tools_read.list_dns_records(api_client, domain_id=domain_id, host=host, record_type=record_type)

@mcp.tool()
def domeneshop_get_dns_record(domain_id: int, record_id: int) -> dict:
    return tools_read.get_dns_record(api_client, domain_id=domain_id, record_id=record_id)

@mcp.tool()
def domeneshop_list_http_forwards(domain_id: int) -> dict:
    return tools_read.list_http_forwards(api_client, domain_id=domain_id)

@mcp.tool()
def domeneshop_get_http_forward(domain_id: int, host: str) -> dict:
    return tools_read.get_http_forward(api_client, domain_id=domain_id, host=host)

@mcp.tool()
def domeneshop_list_invoices(status: str | None = None) -> dict:
    return tools_read.list_invoices(api_client, status=status)

@mcp.tool()
def domeneshop_get_invoice(invoice_id: int) -> dict:
    return tools_read.get_invoice(api_client, invoice_id=invoice_id)

@mcp.tool()
def sftp_list_allowed_roots() -> dict:
    return tools_sftp_read.sftp_list_allowed_roots(remote_client)

@mcp.tool()
def sftp_list_files(remote_path: str) -> dict:
    return tools_sftp_read.sftp_list_files(remote_client, remote_path=remote_path)

@mcp.tool()
def sftp_get_file_metadata(remote_path: str) -> dict:
    return tools_sftp_read.sftp_get_file_metadata(remote_client, remote_path=remote_path)

@mcp.tool()
def sftp_read_text_file(remote_path: str) -> dict:
    return tools_sftp_read.sftp_read_text_file(remote_client, remote_path=remote_path)

@mcp.tool()
def http_check_endpoint(url: str) -> dict:
    return tools_health.http_check_endpoint(health_client, url=url)

@mcp.tool()
def http_check_json_health(url: str) -> dict:
    return tools_health.http_check_json_health(health_client, url=url)

@mcp.tool()
def http_check_tls(url: str) -> dict:
    return tools_health.http_check_tls(health_client, url=url)

@mcp.tool()
def deployment_build_local_manifest(source_root: str) -> dict:
    return tools_dry_run.build_manifest(source_root)

@mcp.tool()
def deployment_compare_manifest(source_root: str, target_root: str, allowed_roots: list[str], remote_metadata: list[dict]) -> dict:
    return tools_dry_run.compare_plan(source_root, target_root, tuple(allowed_roots), remote_metadata)

@mcp.tool()
def recovery_build_backup_manifest(plan_payload: dict, remote_metadata: list[dict], backup_root: str, allowed_roots: list[str]) -> dict:
    return tools_recovery_plan.build_backup_manifest_from_plan(plan_payload, remote_metadata, backup_root, allowed_roots)

@mcp.tool()
def recovery_build_restore_preview(manifest_payload: dict, allowed_roots: list[str]) -> dict:
    return tools_recovery_plan.build_restore_preview_from_manifest(manifest_payload, allowed_roots)

if __name__ == "__main__":
    mcp.run()
