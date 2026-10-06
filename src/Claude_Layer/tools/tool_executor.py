from tools.tools_definition import get_anomaly_score, get_network_summary, get_grid_activity, get_grid_features, get_total_activity

def execute_tool(tool_name, tool_input):

    if tool_name == "get_network_summary":
        return get_network_summary(
            as_of=tool_input.get("as_of")
        )

    if tool_name == "get_grid_activity":
        return get_grid_activity(
            grid_id=tool_input["grid_id"],
            date=tool_input.get("date"),
            hour=tool_input.get("hour"),
            as_of=tool_input.get("as_of")
        )

    if tool_name == "get_grid_features":
        return get_grid_features(
            grid_id=tool_input["grid_id"],
            as_of=tool_input.get("as_of")
        )

    if tool_name == "get_anomaly_score":
        return get_anomaly_score(
            grid_id=tool_input["grid_id"],
            timestamp=tool_input["timestamp"]
        )

    if tool_name == "get_total_activity":
        return get_total_activity(
            grid_id=tool_input["grid_id"]
        )

    raise ValueError(f"Unknown tool: {tool_name}")