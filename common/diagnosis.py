"""The shared diagnosis contract: both systems answer through this tool."""

COMPONENTS = ["nginx", "api", "worker", "postgres", "redis", "other"]
FAULT_TYPES = [
    "process_down",
    "misconfiguration",
    "resource_exhaustion",
    "network",
    "code_bug",
    "other",
]

DIAGNOSIS_TOOL = {
    "name": "submit_diagnosis",
    "description": (
        "Submit your final root-cause diagnosis. Call this exactly once, when "
        "you have reached a conclusion. The suggested fix is advisory only: a "
        "human reviews it and nothing is ever executed automatically."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "root_cause_component": {
                "type": "string",
                "enum": COMPONENTS,
                "description": "The service where the root cause lives (not where symptoms appear).",
            },
            "root_cause_type": {
                "type": "string",
                "enum": FAULT_TYPES,
                "description": "The kind of fault at the root cause.",
            },
            "explanation": {
                "type": "string",
                "description": (
                    "2-6 sentences: the causal chain from root cause to the "
                    "alerted symptom."
                ),
            },
            "evidence": {
                "type": "array",
                "description": "Verbatim quotes that support the diagnosis.",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Where the quote comes from (tool call or evidence section).",
                        },
                        "quote": {
                            "type": "string",
                            "description": "Verbatim excerpt from that source.",
                        },
                    },
                    "required": ["source", "quote"],
                    "additionalProperties": False,
                },
            },
            "suggested_fix": {
                "type": "string",
                "description": "Concrete remediation for a human to review and apply.",
            },
        },
        "required": [
            "root_cause_component",
            "root_cause_type",
            "explanation",
            "evidence",
            "suggested_fix",
        ],
        "additionalProperties": False,
    },
}
