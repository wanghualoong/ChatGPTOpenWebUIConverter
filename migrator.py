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
                n for n in zf.namelist() if n.lower().endswith("conversations.json")
            ]
            if not candidates:
                raise MigrationError(
                    "conversations.json not found in zip. Please export data from ChatGPT first."
                )
            selected = sorted(candidates, key=len)[0]
            return zf.read(selected), selected
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

    if output_path is None:
        output_path = Path.cwd() / "openwebui_import.json"

    try:
        output_path.write_bytes(raw)
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
