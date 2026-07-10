"""
Files API upload stub — upload-once pattern for attachment-a-generator.

This is a STARTING POINT, not a finished script. Wire in the actual list of
source files for the project before running. Requires the `anthropic` Python
SDK (`pip install anthropic --break-system-packages` if needed) and an
ANTHROPIC_API_KEY environment variable.

Splits large PDFs BEFORE running this — see attachment-a-generator Stage 1
guidance. Uploading one 40MB spec manual as a single file works, but per-
division sections make targeted retrieval in Stage 2 drafting cleaner and
cheaper.
"""

import json
import os
from pathlib import Path

import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

# ---- WIRE THIS IN PER PROJECT ----
# Map of a human-readable label -> path relative to 00-source-docs/
SOURCE_FILES = {
    # "rfp": "01-rfp-itb/Notice_of_Request_for_Proposals.pdf",
    # "itb": "01-rfp-itb/Invitation_to_Bid.pdf",
    # "spec-div-01-14": "04-specs-reports/spec-manual-div-01-14.pdf",
    # "spec-div-21-33": "04-specs-reports/spec-manual-div-21-33.pdf",
    # "drawings-civil": "03-drawings/civil-sheets.pdf",
    # "geotech": "04-specs-reports/Geotech_Report.pdf",
    # "asbestos-survey": "04-specs-reports/Asbestos_Survey.pdf",
    # "addendum-1": "06-addenda/Addendum_1.pdf",
    # "clarification-1": "06-addenda/Clarification_No_1.pdf",
    # "clarification-2": "06-addenda/Clarification_No_2.pdf",
}

SOURCE_ROOT = Path("00-source-docs")
OUTPUT_PATH = Path("01-index/file_ids.json")


def upload_all(source_files: dict[str, str]) -> dict[str, dict]:
    """Upload each file once, return a dict of label -> file metadata."""
    results = {}
    for label, rel_path in source_files.items():
        full_path = SOURCE_ROOT / rel_path
        if not full_path.exists():
            print(f"SKIP (not found): {label} -> {full_path}")
            continue
        with open(full_path, "rb") as f:
            uploaded = client.beta.files.upload(
                file=(full_path.name, f, "application/pdf")
            )
        results[label] = {
            "file_id": uploaded.id,
            "filename": uploaded.filename,
            "size_bytes": uploaded.size_bytes,
            "source_path": str(rel_path),
        }
        print(f"Uploaded {label}: {uploaded.id} ({uploaded.filename})")
    return results


def main():
    if not SOURCE_FILES:
        raise SystemExit(
            "SOURCE_FILES is empty — wire in the project's actual file list "
            "before running this script."
        )
    file_ids = upload_all(SOURCE_FILES)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(file_ids, f, indent=2)
    print(f"\nWrote {len(file_ids)} file_id records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
