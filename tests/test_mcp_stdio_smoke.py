import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_stdio_initialize_and_tools_list():
    async def exercise_server() -> set[str]:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "domeneshop_mcp.server"],
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return {tool.name for tool in result.tools}

    tool_names = asyncio.run(exercise_server())

    assert {
        "domeneshop_list_domains",
        "domeneshop_list_dns_records",
        "sftp_list_allowed_roots",
        "http_check_endpoint",
        "deployment_build_local_manifest",
        "control_evaluate_change_preflight",
    }.issubset(tool_names)
    assert "domeneshop_create_dns_txt" not in tool_names
