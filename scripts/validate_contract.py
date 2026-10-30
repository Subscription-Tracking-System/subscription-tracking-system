"""Validate the Sprint 1 OpenAPI draft and every documented payload example."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import OpenAPIV31SpecValidator

ROOT = Path(__file__).resolve().parents[1]
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


class ContractError(ValueError):
    """A document is syntactically valid but unsafe or inconsistent to consume."""


class StrictLoader(yaml.SafeLoader):
    """Reject duplicate and non-string mapping keys instead of silently replacing them."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        mapping: dict = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ContractError(f"YAML keys must be strings (line {key_node.start_mark.line + 1}).")
            if key in mapping:
                raise ContractError(f"Duplicate YAML key {key!r} (line {key_node.start_mark.line + 1}).")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def load_document(path: Path) -> dict[str, Any]:
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictLoader)
    if not isinstance(document, dict):
        raise ContractError("The contract root must be a mapping.")
    return document


def resolve_reference(document: dict, node: dict) -> dict:
    seen: set[str] = set()
    while "$ref" in node:
        reference = node["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise ContractError(f"Only local references are supported: {reference!r}")
        if reference in seen:
            raise ContractError(f"Circular reference: {reference}")
        seen.add(reference)
        target: Any = document
        try:
            for token in reference[2:].split("/"):
                target = target[token.replace("~1", "/").replace("~0", "~")]
        except (KeyError, TypeError) as exc:
            raise ContractError(f"Unresolved reference: {reference}") from exc
        if not isinstance(target, dict):
            raise ContractError(f"Reference must point to an object: {reference}")
        node = {**target, **{key: value for key, value in node.items() if key != "$ref"}}
    return node


def make_validator(document: dict, schema: dict) -> Draft202012Validator:
    # Local references resolve against the contract's components, without network I/O.
    root_schema = {"components": document.get("components", {}), **schema}
    return Draft202012Validator(root_schema, format_checker=FormatChecker())


def walk(value: Any, location: str = "$"):
    if isinstance(value, dict):
        yield location, value
        for key, child in value.items():
            yield from walk(child, f"{location}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{location}/{index}")


def example_values(document: dict, node: dict):
    if "example" in node:
        yield "example", node["example"]
    examples = node.get("examples", {})
    if isinstance(examples, dict):
        for name, example in examples.items():
            resolved = resolve_reference(document, example)
            if "value" not in resolved:
                raise ContractError(f"Example {name!r} must provide a local value.")
            yield name, resolved["value"]
    elif isinstance(examples, list):
        for index, example in enumerate(examples):
            yield str(index), example


def check_payload(document: dict, schema: dict, value: Any, location: str) -> None:
    errors = sorted(make_validator(document, schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        error = errors[0]
        path = "/".join(str(part) for part in error.path) or "<root>"
        raise ContractError(f"{location} at {path}: {error.message}")


def validate_document(document: dict) -> dict[str, Any]:
    if document.get("openapi") != "3.1.0":
        raise ContractError("The agreed Sprint 1 contract must use OpenAPI 3.1.0.")
    if "date-time" not in FormatChecker.checkers:
        raise ContractError("Install rfc3339-validator to enforce date-time formats.")

    for _, node in walk(document):
        if "$ref" in node:
            resolve_reference(document, node)
    OpenAPIV31SpecValidator(document).validate()

    schemas = document.get("components", {}).get("schemas", {})
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    examples_checked = 0
    for location, node in walk(document):
        schema = node.get("schema")
        if schema is None and any(key in node for key in ("type", "allOf", "anyOf", "oneOf")):
            schema = node
        if isinstance(schema, dict):
            for name, value in example_values(document, node):
                check_payload(document, schema, value, f"{location}/{name}")
                examples_checked += 1

    operations: list[str] = []
    for path, path_item in document.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            operations.append(f"{method.upper()} {path}")
            for status, response_ref in operation.get("responses", {}).items():
                response = resolve_reference(document, response_ref)
                if status == "204" and "content" in response:
                    raise ContractError(f"{method.upper()} {path}: 204 must have no response body.")
                for media_type, media in response.get("content", {}).items():
                    for name, value in example_values(document, media):
                        check_payload(document, media["schema"], value, f"{method} {path}/{status}/{name}")
                        if media_type == "application/problem+json" and str(value.get("status")) != status:
                            raise ContractError(f"{method.upper()} {path}: problem status must equal HTTP {status}.")

    return {
        "result": "passed",
        "openapi": document["openapi"],
        "contract_version": document["info"]["version"],
        "operations": operations,
        "schemas_checked": len(schemas),
        "documented_examples_checked": examples_checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=ROOT / "api" / "openapi.yaml")
    parser.add_argument("--report", type=Path, help="Optional JSON evidence report")
    arguments = parser.parse_args()
    try:
        result = validate_document(load_document(arguments.contract))
    except Exception as exc:
        print(f"Contract validation failed: {exc}", file=sys.stderr)
        return 1
    if arguments.report:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: OpenAPI {result['openapi']}; {len(result['operations'])} operations; "
          f"{result['schemas_checked']} schemas; {result['documented_examples_checked']} documented examples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
