tools = [
    {
        "name": "get_network_summary",
        "description": "Get the current overall network summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "as_of": {
                    "type": "string",
                    "description": "Optional ISO timestamp."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_grid_activity",
        "description": "Get the activity history for a specific grid over a 24-hour window.",
        "input_schema": {
            "type": "object",
            "properties": {
                "grid_id": {
                    "type": "integer"
                },
                "date": {
                    "type": "string"
                },
                "hour": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 23
                },
                "as_of": {
                    "type": "string"
                }
            },
            "required": ["grid_id"]
        }
    },
    {
        "name": "get_grid_features",
        "description": "Get calculated features for a specific grid using its latest 24-hour activity window.",
        "input_schema": {
            "type": "object",
            "properties": {
                "grid_id": {
                    "type": "integer"
                },
                "as_of": {
                    "type": "string"
                }
            },
            "required": ["grid_id"]
        }
    },
    {
        "name": "get_anomaly_score",
        "description": "Get the anomaly score for a grid at an exact timestamp.",
        "input_schema": {
            "type": "object",
            "properties": {
                "grid_id": {
                    "type": "integer"
                },
                "timestamp": {
                    "type": "string"
                }
            },
            "required": ["grid_id", "timestamp"]
        }
    },
    {
        "name": "get_total_activity",
        "description": "Get total activity for a specific grid.",
        "input_schema": {
            "type": "object",
            "properties": {
                "grid_id": {
                    "type": "integer"
                }
            },
            "required": ["grid_id"]
        }
    }
]