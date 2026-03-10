def get_tools():
    return [
        {
            "type": "function",
            "name": "fetch_datas",
            "description": (
                "Fetch data from a supported source by URL. Use when the user gives a new data-source URL, "
                "or when the user asks to regenerate or change the Compare view (different comparison, metric, dimension, or segment) "
                "and a data-source URL already exists in the conversation—then use the most recent URL from the conversation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source_kind": {
                        "type": "string",
                        "description": "Provider for the data source.",
                        "enum": ["google_sheet"],
                    },
                    "url": {
                        "type": "string",
                        "description": (
                            "Full URL of the data source. When the user asks to change the graph without a new URL, "
                            "use the most recent data-source URL from the conversation."
                        ),
                    },
                },
                "required": ["source_kind", "url"],
            },
        }
    ]
