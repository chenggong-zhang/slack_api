from __future__ import annotations

def tool_definitions() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "add_channels",
                "description": "Subscribe the user to one or more Slack channel IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "channels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Channel IDs like C12345",
                        }
                    },
                    "required": ["channels"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "remove_channels",
                "description": "Unsubscribe the user from one or more Slack channel IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {"channels": {"type": "array", "items": {"type": "string"}}},
                    "required": ["channels"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "set_max_channels",
                "description": "Set the maximum number of channels to track for this user.",
                "parameters": {
                    "type": "object",
                    "properties": {"max_channels": {"type": "integer", "minimum": 1, "maximum": 50}},
                    "required": ["max_channels"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "set_digest_time",
                "description": "Change daily digest time in the user's local HH:MM format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_local": {
                            "type": "string",
                            "pattern": "^([01]?\\d|2[0-3]):[0-5]\\d$",
                        }
                    },
                    "required": ["time_local"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "set_preferences",
                "description": "Toggle digest sections or update custom rules.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_overview": {"type": "boolean"},
                        "include_mentions_me": {"type": "boolean"},
                        "include_broadcasts": {"type": "boolean"},
                        "include_unanswered_questions": {"type": "boolean"},
                        "include_suggested_actions": {"type": "boolean"},
                        "custom_rules_json": {"type": "object"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_configuration",
                "description": "Return the user's current tracking configuration.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]
