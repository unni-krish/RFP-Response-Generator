"""
Intake Agent

Validates incoming RFP documents and generates
structured metadata for downstream agents.
"""

from pathlib import Path
import json

from pypdf import PdfReader
from docx import Document
import sys
import os

# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import load_config

config = load_config()
paths_config = config.get("paths", {})
INPUT_FOLDER = paths_config.get("input_folder", "input")

intake_config = config.get("intake", {})

SUPPORTED_TYPES = intake_config.get("supported_types", [".pdf", ".docx", ".doc"])
MAX_FILE_SIZE_MB = intake_config.get("max_file_size_mb", 50)


def validate_pdf(file_path):
    """
    Check whether PDF can be opened.
    """

    try:
        PdfReader(file_path)
        return True

    except Exception:
        return False


def validate_docx(file_path):
    """
    Check whether DOCX can be opened.
    """

    try:
        Document(file_path)
        return True

    except Exception:
        return False


def validate_file(file_path):

    result = {
        "file_name": file_path.name,
        "file_type": file_path.suffix,
        "status": "VALID",
        "errors": []
    }

    # --------------------------
    # Extension Validation
    # --------------------------

    if file_path.suffix.lower() not in SUPPORTED_TYPES:

        result["status"] = "INVALID"

        result["errors"].append(
            "Unsupported file type"
        )

    # --------------------------
    # Empty File Validation
    # --------------------------

    file_size_bytes = file_path.stat().st_size

    if file_size_bytes == 0:

        result["status"] = "INVALID"

        result["errors"].append(
            "Empty file"
        )

    # --------------------------
    # File Size Validation
    # --------------------------

    file_size_mb = file_size_bytes / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:

        result["status"] = "INVALID"

        result["errors"].append(
            f"File size exceeds {MAX_FILE_SIZE_MB} MB"
        )

    # --------------------------
    # PDF Validation
    # --------------------------

    if (
        file_path.suffix.lower() == ".pdf"
        and file_size_bytes > 0
    ):

        if not validate_pdf(file_path):

            result["status"] = "INVALID"

            result["errors"].append(
                "Corrupted PDF"
            )

    # --------------------------
    # DOCX Validation
    # --------------------------

    if (
        file_path.suffix.lower() == ".docx"
        and file_size_bytes > 0
    ):

        if not validate_docx(file_path):

            result["status"] = "INVALID"

            result["errors"].append(
                "Corrupted DOCX"
            )

    result["size_mb"] = round(file_size_mb, 2)

    return result


def process_folder(folder_path):

    results = []

    for file in Path(folder_path).iterdir():

        if file.is_file():

            result = validate_file(file)

            results.append(result)

    return results


if __name__ == "__main__":

    input_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), INPUT_FOLDER)

    results = process_folder(input_folder)

    print("\n===== INTAKE AGENT RESULTS =====\n")

    for item in results:

        print(item)