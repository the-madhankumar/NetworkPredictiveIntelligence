from mcp.server.fastmcp import FastMCP
from api_client import NetworkAPIClient
from validation import validate_grid_id, validate_limit

mcp = FastMCP("network-intelligence")

client = NetworkAPIClient()

@mcp.tool()
async def network_summary() -> dict:
    """Return the network summary from the existing API."""
    return await client.get("/network/summary")

@mcp.tool()
async def grid_activity(grid_id: int) -> dict:
    """Return activity information for a network grid."""
    grid_id = validate_grid_id(grid_id)

    return await client.get(f"/network/grid/{grid_id}")

@mcp.tool()
async def grid_features(grid_id: int) -> dict:
    """Return ML/network features for a network grid."""
    grid_id = validate_grid_id(grid_id)

    return await client.get(f"/network/grid/{grid_id}/features")

@mcp.tool()
async def grid_location(grid_id: int) -> dict:
    """Return geographic information for a network grid."""
    grid_id = validate_grid_id(grid_id)

    return await client.get(f"/network/grid/{grid_id}/location")

@mcp.tool()
async def hotspots(limit: int = 20) -> dict:
    """Return network hotspots from the existing API."""
    limit = validate_limit(limit)

    return await client.get("/network/hotspots", params={"limit": limit})

@mcp.tool()
async def alerts(limit: int = 50) -> dict:
    """Return network alerts from the existing API."""
    limit = validate_limit(limit)

    return await client.get(
        "/network/alerts",
        params={"limit": limit},
    )

@mcp.tool()
async def pipeline_status() -> dict:
    """Return the current data pipeline status."""
    return await client.get("/pipeline/status")

if __name__ == "__main__":
    mcp.run(transport="stdio")