import json
import re
import time
from pathlib import Path
from typing import Any

import litellm
from jinja2 import StrictUndefined, Template
from minisweagent.environments.local import LocalEnvironment, LocalEnvironmentConfig
from minisweagent.exceptions import FormatError, Submitted
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.utils.actions_toolcall import BASH_TOOL


SUBMIT_FAULT_LOCALIZATION_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_fault_localization",
        "description": "Submit the final Top-10 ranked fault-localization predictions.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "predictions": {
                    "type": "array",
                    "minItems": 10,
                    "maxItems": 10,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "class": {
                                "type": "string",
                                "description": "Fully qualified production class name.",
                            },
                            "method": {
                                "type": "string",
                                "description": "Production method name in that class.",
                            },
                        },
                        "required": ["class", "method"],
                    },
                },
                "evidence_chain": {
                    "type": "array",
                    "maxItems": 20,
                    "description": (
                        "Optional concise, agent-reported evidence and inference summaries. "
                        "This is not hidden chain-of-thought and does not affect ranking validity."
                    ),
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "evidence": {"type": "string"},
                            "inference_summary": {"type": "string"},
                            "candidate_methods": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "references": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "file": {"type": "string"},
                                        "line_start": {"type": ["integer", "null"]},
                                        "line_end": {"type": ["integer", "null"]},
                                    },
                                    "required": ["file"],
                                },
                            },
                        },
                    },
                },
            },
            "required": ["predictions"],
        },
    },
}


class FaultLocalizationModel(LitellmModel):
    def _query(self, messages: list[dict[str, str]], **kwargs):
        try:
            return litellm.completion(
                model=self.config.model_name,
                messages=messages,
                tools=[BASH_TOOL, SUBMIT_FAULT_LOCALIZATION_TOOL],
                **(self.config.model_kwargs | kwargs),
            )
        except litellm.exceptions.AuthenticationError as e:
            e.message += " You can permanently set your API key with `mini-extra config set KEY VALUE`."
            raise e

    def _parse_actions(self, response) -> list[dict]:
        tool_calls = response.choices[0].message.tool_calls or []
        if not tool_calls:
            raise FormatError(
                {
                    "role": "user",
                    "content": Template(self.config.format_error_template, undefined=StrictUndefined).render(
                        error="No tool calls found in the response. Every response MUST include at least one tool call.",
                        actions=[],
                        has_tool_calls=False,
                        finish_reason=response.choices[0].finish_reason,
                    ),
                    "extra": {"interrupt_type": "FormatError"},
                }
            )

        actions = []
        for tool_call in tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except Exception as e:
                if name == "submit_fault_localization":
                    actions.append(
                        {
                            "tool": "submit_fault_localization",
                            "payload_error": f"Error parsing tool call arguments: {e}.",
                            "predictions": None,
                            "evidence_chain": None,
                            "tool_call_id": tool_call.id,
                        }
                    )
                    continue
                raise self._format_error(f"Error parsing tool call arguments: {e}.", response) from e

            if name == "bash":
                if not isinstance(args, dict) or "command" not in args:
                    raise self._format_error("Missing 'command' argument in bash tool call.", response)
                actions.append({"command": args["command"], "tool_call_id": tool_call.id})
            elif name == "submit_fault_localization":
                actions.append(
                    {
                        "tool": "submit_fault_localization",
                        "predictions": args.get("predictions") if isinstance(args, dict) else None,
                        "evidence_chain": args.get("evidence_chain") if isinstance(args, dict) else None,
                        "tool_call_id": tool_call.id,
                    }
                )
            else:
                raise self._format_error(f"Unknown tool '{name}'.", response)
        return actions

    def _format_error(self, error: str, response) -> FormatError:
        return FormatError(
            {
                "role": "user",
                "content": Template(self.config.format_error_template, undefined=StrictUndefined).render(
                    actions=[],
                    error=error.strip(),
                    has_tool_calls=True,
                    finish_reason=response.choices[0].finish_reason,
                ),
                "extra": {"interrupt_type": "FormatError"},
            }
        )


class FaultLocalizationEnvironmentConfig(LocalEnvironmentConfig):
    method_catalog_path: str = ""
    submission_output_path: str = ""


class FaultLocalizationEnvironment(LocalEnvironment):
    def __init__(self, *, config_class: type = FaultLocalizationEnvironmentConfig, **kwargs):
        super().__init__(config_class=config_class, **kwargs)
        self._catalog: dict[str, dict[str, Any]] | None = None

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        if action.get("tool") == "submit_fault_localization":
            return self._submit_fault_localization(action)
        return super().execute(action, cwd=cwd, timeout=timeout)

    def _load_catalog(self) -> dict[str, dict[str, Any]]:
        if self._catalog is not None:
            return self._catalog
        catalog_path = Path(self.config.method_catalog_path)
        data = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
        methods = data.get("methods", [])
        self._catalog = {
            f"{entry.get('class', '')}::{entry.get('method', '')}": entry
            for entry in methods
            if entry.get("source_type") == "production"
        }
        return self._catalog

    def _submit_fault_localization(self, action: dict) -> dict[str, Any]:
        validation = self._validate_submission(action)
        if not validation["ok"]:
            return {
                "output": json.dumps(validation, indent=2),
                "returncode": 1,
                "exception_info": "fault-localization submission rejected",
                "extra": {
                    "fault_localization_submission": validation,
                    "tool": "submit_fault_localization",
                },
            }

        output_path = Path(self.config.submission_output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
        raise Submitted(
            {
                "role": "exit",
                "content": json.dumps(validation),
                "extra": {
                    "exit_status": "Submitted",
                    "submission": json.dumps(validation),
                    "fault_localization_submission": validation,
                },
            }
        )

    def _validate_submission(self, action: dict) -> dict[str, Any]:
        catalog = self._load_catalog()
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        if action.get("payload_error"):
            errors.append({"code": "malformed_payload", "message": action["payload_error"]})
        predictions = action.get("predictions")
        if not isinstance(predictions, list):
            errors.append({"code": "invalid_schema", "message": "predictions must be an array"})
            predictions = []
        if len(predictions) != 10:
            errors.append(
                {
                    "code": "invalid_count",
                    "message": "exactly 10 predictions are required",
                    "count": len(predictions),
                }
            )

        normalized = []
        seen = set()
        classes = {entry.get("class", "") for entry in catalog.values()}
        class_method_re = re.compile(r"^[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*$")
        method_re = re.compile(r"^[A-Za-z_$][\w$]*$")
        for index, item in enumerate(predictions, start=1):
            if not isinstance(item, dict):
                errors.append({"code": "invalid_schema", "rank": index, "message": "prediction must be an object"})
                continue
            class_name = str(item.get("class", "")).strip()
            method_name = str(item.get("method", "")).strip()
            key = f"{class_name}::{method_name}"
            if not class_method_re.match(class_name) or not method_re.match(method_name):
                errors.append({"code": "invalid_schema", "rank": index, "message": "invalid class or method name"})
                continue
            if key in seen:
                errors.append({"code": "duplicate_method", "rank": index, "method": key})
            seen.add(key)
            if _looks_like_test_method(class_name, method_name):
                errors.append({"code": "test_method", "rank": index, "method": key})
            if key not in catalog:
                if class_name in classes:
                    errors.append({"code": "method_not_found", "rank": index, "method": key})
                else:
                    errors.append({"code": "class_not_found", "rank": index, "method": key})
            else:
                entry = catalog[key]
                if entry.get("source_type") != "production":
                    errors.append({"code": "non_production_source", "rank": index, "method": key})
            normalized.append({"rank": index, "class": class_name, "method": method_name})

        evidence_chain = self._normalize_evidence_chain(action.get("evidence_chain"), warnings)

        return {
            "schema_version": "d4j-fl-submission/v1",
            "ok": not errors,
            "tool": "submit_fault_localization",
            "prediction_count": len(normalized),
            "predictions": normalized,
            "evidence_chain": evidence_chain,
            "errors": errors,
            "warnings": warnings,
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def _normalize_evidence_chain(
        self, value: Any, warnings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if value is None:
            return []
        if not isinstance(value, list):
            warnings.append(
                {
                    "code": "invalid_evidence_chain",
                    "message": "evidence_chain was ignored because it is not an array",
                }
            )
            return []
        if len(value) > 20:
            warnings.append(
                {
                    "code": "evidence_chain_truncated",
                    "message": "evidence_chain was truncated to 20 items",
                }
            )

        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(value[:20], start=1):
            if not isinstance(item, dict):
                warnings.append(
                    {
                        "code": "invalid_evidence_chain_item",
                        "index": index,
                        "message": "item was ignored because it is not an object",
                    }
                )
                continue
            evidence = str(item.get("evidence", "")).strip()
            inference_summary = str(item.get("inference_summary", "")).strip()
            if not evidence and not inference_summary:
                warnings.append(
                    {
                        "code": "empty_evidence_chain_item",
                        "index": index,
                        "message": "item was ignored because it has no evidence or inference summary",
                    }
                )
                continue
            candidate_methods = item.get("candidate_methods", [])
            if not isinstance(candidate_methods, list):
                candidate_methods = []
                warnings.append(
                    {
                        "code": "invalid_candidate_methods",
                        "index": index,
                        "message": "candidate_methods was ignored because it is not an array",
                    }
                )
            references = item.get("references", [])
            if not isinstance(references, list):
                references = []
            normalized.append(
                {
                    "evidence": evidence,
                    "inference_summary": inference_summary,
                    "candidate_methods": [str(method).strip() for method in candidate_methods if str(method).strip()],
                    "references": [
                        {
                            "file": str(reference.get("file", "")).strip(),
                            "line_start": reference.get("line_start") if isinstance(reference.get("line_start"), int) else None,
                            "line_end": reference.get("line_end") if isinstance(reference.get("line_end"), int) else None,
                        }
                        for reference in references
                        if isinstance(reference, dict) and str(reference.get("file", "")).strip()
                    ],
                }
            )
        return normalized


def _looks_like_test_method(class_name: str, method_name: str) -> bool:
    return (
        class_name.endswith("Test")
        or class_name.endswith("Tests")
        or ".junit." in class_name
        or ".test." in class_name
        or method_name.startswith("test")
    )
