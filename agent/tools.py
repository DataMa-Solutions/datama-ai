def get_tools():
    return [
        {
            "type": "function",
            "name": "prepare_datama_context",
            "description": (
                "Fetch data and set the Datama solution context. Use when the user gives a new data-source URL, "
                "or when the user asks to regenerate or change the Datama view (different comparison, metric, dimension, or segment) "
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
                    "solution": {
                        "type": "string",
                        "description": "Datama solution to render for this request.",
                        "enum": ["compare", "explore"],
                    },
                    "url": {
                        "type": "string",
                        "description": (
                            "Full URL of the data source. When the user asks to change the graph without a new URL, "
                            "use the most recent data-source URL from the conversation."
                        ),
                    },
                },
                "required": ["source_kind", "solution", "url"],
            },
        }
    ]
