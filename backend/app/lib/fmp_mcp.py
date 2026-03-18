"""FMP MCP Server client manager.

Manages the lifecycle of the Financial Modeling Prep MCP server subprocess
and provides a persistent client session for tool discovery and execution.

Requires:
  - Node.js / npx available on PATH
  - pip install mcp>=1.0.0
  - FMP API key (same key used by OpenBB)
"""
import asyncio
import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# Toolsets to enable (complements existing OpenBB tools)
# Full list: company,quotes,statements,calendar,charts,news,analyst,market-performance,
#            insider-trades,institutional,indexes,economics,crypto,forex,commodities,
#            etf-funds,esg,technical-indicators,senate,sec-filings,earnings,dcf,bulk,search
DEFAULT_TOOL_SETS = "analyst,news,statements,insider-trades,earnings,dcf"

# Port for the FMP MCP HTTP server (must not conflict with main app on 6900)
FMP_MCP_PORT = 8765


class FMPMCPManager:
    """Manages the FMP MCP server subprocess and a persistent MCP client session."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._session = None
        self._task: Optional[asyncio.Task] = None
        self._tools_cache: list[dict] = []
        self._fmp_tool_names: set[str] = set()
        self._connected = asyncio.Event()
        self._port = FMP_MCP_PORT
        self.ready = False

    async def start(self, api_key: str) -> bool:
        """Start the FMP MCP server subprocess and connect to it.

        Returns True on success, False if unavailable (e.g. no Node.js).
        The agent continues with built-in tools only when this returns False.
        """
        if not api_key:
            logger.info("FMP MCP: no API key configured, skipping")
            return False

        try:
            env = {
                **os.environ,
                "FMP_ACCESS_TOKEN": api_key,
                "PORT": str(self._port),
                "FMP_TOOL_SETS": DEFAULT_TOOL_SETS,
            }
            self._process = subprocess.Popen(
                ["npx", "-y", "financial-modeling-prep-mcp-server"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(
                f"FMP MCP server starting on port {self._port} (PID: {self._process.pid})"
            )

            # Give the Node.js process time to bind the port
            await asyncio.sleep(5)

            if self._process.poll() is not None:
                logger.error("FMP MCP server exited immediately after starting")
                return False

            self._connected.clear()
            self._task = asyncio.create_task(self._maintain_connection())

            try:
                await asyncio.wait_for(self._connected.wait(), timeout=30)
                self.ready = True
                return True
            except asyncio.TimeoutError:
                logger.error("FMP MCP: timed out waiting for SSE connection")
                await self.stop()
                return False

        except FileNotFoundError:
            logger.warning(
                "FMP MCP: 'npx' not found — install Node.js to enable FMP MCP tools"
            )
            return False
        except Exception as e:
            logger.error(f"FMP MCP startup failed: {e}")
            return False

    async def _maintain_connection(self):
        """Background task: holds the SSE connection open for the app lifetime."""
        try:
            from mcp.client.sse import sse_client
            from mcp import ClientSession

            async with sse_client(f"http://localhost:{self._port}/sse") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self._session = session
                    self._connected.set()
                    # Block indefinitely to keep the connection alive
                    await asyncio.get_event_loop().create_future()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"FMP MCP connection lost: {e}")
            self._session = None
            self.ready = False

    async def stop(self):
        """Terminate the FMP MCP server and clean up."""
        self.ready = False
        self._session = None

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            logger.info("FMP MCP server stopped")

    async def get_tools(self) -> list[dict]:
        """Return FMP MCP tools in Anthropic tool format (cached after first call)."""
        if not self.ready or not self._session:
            return []

        if self._tools_cache:
            return self._tools_cache

        try:
            result = await self._session.list_tools()
            self._tools_cache = [
                {
                    "name": tool.name,
                    "description": tool.description or f"FMP: {tool.name}",
                    "input_schema": tool.inputSchema,
                }
                for tool in result.tools
            ]
            self._fmp_tool_names = {t["name"] for t in self._tools_cache}
            logger.info(f"FMP MCP: {len(self._tools_cache)} tools loaded")
            return self._tools_cache
        except Exception as e:
            logger.error(f"FMP MCP get_tools failed: {e}")
            return []

    async def call_tool(self, name: str, args: dict) -> str:
        """Execute an FMP MCP tool and return the result as a string."""
        if not self.ready or not self._session:
            return f"FMP MCP unavailable: cannot call '{name}'"

        try:
            result = await self._session.call_tool(name, args)
            parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    parts.append(content.text)
                elif hasattr(content, "data"):
                    parts.append(str(content.data))
            return "\n".join(parts) if parts else "No result returned"
        except Exception as e:
            logger.error(f"FMP MCP call_tool({name}) failed: {e}")
            return f"Error calling FMP tool '{name}': {str(e)}"

    def is_fmp_tool(self, tool_name: str) -> bool:
        """Return True if the tool name belongs to the FMP MCP server."""
        return tool_name in self._fmp_tool_names


# Singleton used across the app
fmp_mcp = FMPMCPManager()
