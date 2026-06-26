"""MCP server entrypoint for Domeneshop Phase 2 read tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from . import tools_read


mcp = FastMCP("domeneshop-mcp")
_config = DomeneshopConfig.from_env()
_client = DomeneshopReadClient(_config)


@mcp.tool()
def domeneshop_list_domains(domain: str | None = None) -> dict:
    return tools_read.list_domains(_client, domain=domain)


@mcp.tool()
def domeneshop_get_domain(domain_id: int) -> dict:
    return tools_read.get_domain(_client, domain_id=domain_id)


@mcp.tool()
def domeneshop_list_dns_records(domain_id: int, host: str | None = None, record_type: str | None = None) -> dict:
    return tools_read.list_dns_records(_client, domain_id=domain_id, host=host, record_type=record_type)


@mcp.tool()
def domeneshop_get_dns_record(domain_id: int, record_id: int) -> dict:
    return tools_read.get_dns_record(_client, domain_id=domain_id, record_id=record_id)


@mcp.tool()
def domeneshop_list_http_forwards(domain_id: int) -> dict:
    return tools_read.list_http_forwards(_client, domain_id=domain_id)


@mcp.tool()
def domeneshop_get_http_forward(domain_id: int, host: str) -> dict:
    return tools_read.get_http_forward(_client, domain_id=domain_id, host=host)


@mcp.tool()
def domeneshop_list_invoices(status: str | None = None) -> dict:
    return tools_read.list_invoices(_client, status=status)


@mcp.tool()
def domeneshop_get_invoice(invoice_id: int) -> dict:
    return tools_read.get_invoice(_client, invoice_id=invoice_id)


if __name__ == "__main__":
    mcp.run()
