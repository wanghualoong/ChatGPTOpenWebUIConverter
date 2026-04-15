#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Tuple


class MigrationError(Exception):
    pass


def _load_json_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise MigrationError(f"Cannot read file: {path}") from exc


def _find_conversations_in_zip(path: Path) -> Tuple[bytes, str]:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            candidates = [
                n
                for n in zf.namelist()
                if Path(n).name.lower() == "conversations.json"
            ]
            if candidates:
                selected = sorted(candidates, key=len)[0]
                return zf.read(selected), selected

            # New ChatGPT exports can shard conversations into:
            # conversations-000.json, conversations-001.json, ...
            # and provide file mapping in export_manifest.json.
            if "export_manifest.json" in zf.namelist():
                try:
                    manifest = json.loads(zf.read("export_manifest.json"))
                except json.JSONDecodeError as exc:
                    raise MigrationError("export_manifest.json is invalid.") from exc

                logical_files = manifest.get("logical_files")
                if isinstance(logical_files, dict):
                    convo = logical_files.get("conversations.json")
                    shard_files = convo.get("files") if isinstance(convo, dict) else None
                    if isinstance(shard_files, list) and shard_files:
                        merged: list[Any] = []
                        for fname in shard_files:
                            if not isinstance(fname, str):
                                continue
                            try:
                                chunk = json.loads(zf.read(fname))
                            except KeyError as exc:
                                raise MigrationError(
                                    f"Shard file listed in manifest not found: {fname}"
                                ) from exc
                            except json.JSONDecodeError as exc:
                                raise MigrationError(
                                    f"Shard file is invalid JSON: {fname}"
                                ) from exc

                            if isinstance(chunk, list):
                                merged.extend(chunk)
                            else:
                                raise MigrationError(
                                    f"Shard file format unsupported (expected list): {fname}"
                                )

                        return (
                            json.dumps(merged, ensure_ascii=False).encode("utf-8"),
                            "merged:" + ",".join(shard_files),
                        )

            # Fallback: merge conversations-*.json if present, even without manifest.
            shard_candidates = sorted(
                n for n in zf.namelist() if n.lower().startswith("conversations-") and n.lower().endswith(".json")
            )
            if shard_candidates:
                merged: list[Any] = []
                for fname in shard_candidates:
                    try:
                        chunk = json.loads(zf.read(fname))
                    except json.JSONDecodeError as exc:
                        raise MigrationError(f"Shard file is invalid JSON: {fname}") from exc
                    if isinstance(chunk, list):
                        merged.extend(chunk)
                    else:
                        raise MigrationError(
                            f"Shard file format unsupported (expected list): {fname}"
                        )

                return (
                    json.dumps(merged, ensure_ascii=False).encode("utf-8"),
                    "merged:" + ",".join(shard_candidates),
                )

            raise MigrationError(
                "conversations.json not found in zip, and no shard conversations-*.json found."
            )
    except zipfile.BadZipFile as exc:
        raise MigrationError(f"Invalid zip file: {path}") from exc


def _validate_chatgpt_export_json(raw: bytes) -> None:
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MigrationError("Input JSON is invalid.") from exc

    if isinstance(data, list):
        if not data:
            raise MigrationError("Input JSON is empty.")
        sample = data[0]
        if not isinstance(sample, dict) or "mapping" not in sample:
            raise MigrationError(
                "Input JSON does not look like ChatGPT conversations export."
            )
        return

    if isinstance(data, dict) and "conversations" in data:
        return

    raise MigrationError("Unsupported JSON structure for OpenWebUI import.")


def _infer_conversation_model(conversation: dict[str, Any]) -> str | None:
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return None

    # Prefer the most recent assistant message model_slug.
    best: tuple[float, str] | None = None
    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        author = message.get("author")
        role = author.get("role") if isinstance(author, dict) else None
        if role != "assistant":
            continue
        metadata = message.get("metadata")
        model_slug = metadata.get("model_slug") if isinstance(metadata, dict) else None
        if not isinstance(model_slug, str) or not model_slug.strip() or model_slug == "auto":
            continue
        create_time = message.get("create_time")
        ts = float(create_time) if isinstance(create_time, (int, float)) else -1.0
        candidate = model_slug.strip()
        if best is None or ts >= best[0]:
            best = (ts, candidate)

    return best[1] if best else None


def _normalize_chatgpt_export_json(raw: bytes) -> bytes:
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MigrationError("Input JSON is invalid.") from exc

    def patch_list(conversations: list[Any]) -> None:
        for item in conversations:
            if not isinstance(item, dict):
                continue
            if "mapping" not in item:
                continue
            current = item.get("default_model_slug")
            if isinstance(current, str) and current.strip() and current.strip() != "auto":
                continue
            inferred = _infer_conversation_model(item)
            if inferred:
                item["default_model_slug"] = inferred

    if isinstance(data, list):
        patch_list(data)
    elif isinstance(data, dict):
        conversations = data.get("conversations")
        if isinstance(conversations, list):
            patch_list(conversations)

    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def prepare_input(input_path: Path, output_path: Path | None) -> Path:
    suffix = input_path.suffix.lower()
    raw: bytes
    src_name = input_path.name

    if suffix == ".zip":
        raw, src_name = _find_conversations_in_zip(input_path)
    elif suffix == ".json":
        raw = _load_json_bytes(input_path)
    else:
        raise MigrationError("Input file must be .zip or .json")

    _validate_chatgpt_export_json(raw)
    normalized = _normalize_chatgpt_export_json(raw)
    _validate_chatgpt_export_json(normalized)

    if output_path is None:
        output_path = Path.cwd() / "openwebui_import.json"

    try:
        output_path.write_bytes(normalized)
    except OSError as exc:
        raise MigrationError(f"Cannot write output file: {output_path}") from exc

    print(f"Prepared file: {output_path} (source: {src_name})")
    print("Next step: OpenWebUI -> Settings -> Data Controls -> Import Chats")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare ChatGPT export into a file for manual import in OpenWebUI "
            "(tested for OpenWebUI v0.8.12)."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser(
        "prepare", help="Extract/validate conversations JSON for OpenWebUI manual import"
    )
    p_prepare.add_argument(
        "--input", required=True, help="ChatGPT export .zip or conversations.json"
    )
    p_prepare.add_argument("--output", help="Output path (default: ./openwebui_import.json)")

    p_migrate = sub.add_parser(
        "migrate",
        help="Alias of prepare (kept for compatibility)",
    )
    p_migrate.add_argument(
        "--input", required=True, help="ChatGPT export .zip or conversations.json"
    )
    p_migrate.add_argument("--output", help="Output path (default: ./openwebui_import.json)")

    return parser.parse_args()


def run() -> int:
    args = parse_args()

    try:
        if args.command in {"prepare", "migrate"}:
            output = Path(args.output).expanduser() if args.output else None
            prepare_input(Path(args.input).expanduser(), output)
            return 0

        raise MigrationError("Unknown command")

    except MigrationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
