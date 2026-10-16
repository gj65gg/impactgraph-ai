
import re

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP

from app.servicenow import ServiceNowClient
from app.graph import DependencyGraph


mcp = FastMCP(
    "ImpactGraph",
    host="127.0.0.1",
    port=8000
)


def validate(sys_id):
    if not re.fullmatch(
        r"[a-fA-F0-9]{32}",
        sys_id
    ):
        raise ValueError("Invalid sys_id")


@mcp.tool()
def get_component(sys_id: str) -> dict:
    """
    Retrieve a Script Include from ServiceNow.
    """
    validate(sys_id)

    snow = ServiceNowClient()

    try:
        return (
            snow.get_script_include(sys_id)
            or {"error": "not found"}
        )
    finally:
        snow.close()


@mcp.tool()
def get_change_impact(
    sys_id: str,
    depth: int = 3
) -> dict:
    """
    Retrieve candidate downstream dependents
    from the Neo4j dependency graph.
    """
    validate(sys_id)

    graph = DependencyGraph()

    try:
        impacted = graph.get_impact(
            sys_id,
            depth
        )

        return {
            "component": sys_id,
            "impacted": impacted,
            "count": len(impacted),
            "evidence_status": "candidate",
            "coverage": (
                "Constructor references "
                "in scanned scripts only"
            )
        }

    finally:
        graph.close()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
