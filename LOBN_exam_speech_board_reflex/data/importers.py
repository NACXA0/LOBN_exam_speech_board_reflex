# Importers for different file formats

from __future__ import annotations

import os
import base64
import re
from typing import Optional, Tuple

from LOBN_exam_speech_board_reflex.data.question_bank import (
    QuestionBank,
    normalize_question_bank,
    TEMP_DIR,
    ensure_directories,
)


def import_text_content(text: str, filename: str = "imported.txt") -> QuestionBank:
    """Import question bank from plain text content."""
    bank = parse_text_to_bank(text, filename)
    return normalize_question_bank(bank)


def import_markdown_content(content: str, filename: str = "imported.md") -> QuestionBank:
    """Import question bank from markdown content."""
    from LOBN_exam_speech_board_reflex.data.question_bank import parse_markdown_to_bank
    bank = parse_markdown_to_bank(content, filename)
    return normalize_question_bank(bank)


def import_json_content(content: str, filename: str = "imported.json") -> QuestionBank:
    """Import question bank from JSON content."""
    import json
    data = json.loads(content)
    if isinstance(data, list):
        # Array of questions format
        questions = []
        for item in data:
            questions.append({
                "question": item.get("question", item.get("题干", "")),
                "options": item.get("options", item.get("选项", [])),
                "answer": item.get("answer", item.get("答案", "")),
                "explanation": item.get("explanation", item.get("解析", "")),
                "images": item.get("images", item.get("图片", [])),
            })
    elif isinstance(data, dict):
        # Object format with questions array
        questions_list = data.get("questions", data.get("题库", []))
        questions = []
        for item in questions_list:
            questions.append({
                "question": item.get("question", item.get("题干", "")),
                "options": item.get("options", item.get("选项", [])),
                "answer": item.get("answer", item.get("答案", "")),
                "explanation": item.get("explanation", item.get("解析", "")),
                "images": item.get("images", item.get("图片", [])),
            })
    else:
        raise ValueError("Invalid JSON structure")

    name = os.path.splitext(filename)[0]
    from LOBN_exam_speech_board_reflex.data.question_bank import QuestionBank
    bank = QuestionBank(name=name, filename=filename, questions=questions)
    return normalize_question_bank(bank)


def import_docx_content(file_path: str, filename: str = "imported.docx") -> QuestionBank:
    """Import question bank from DOCX file."""
    try:
        import docx
        doc = docx.Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs])
        return parse_text_to_bank(content, filename)
    except ImportError:
        raise ImportError("python-docx is required for DOCX import. Install with: pip install python-docx")


def parse_text_to_bank(content: str, filename: str = "imported.txt") -> QuestionBank:
    """Parse plain text content into a QuestionBank.

    Supports formats:
    - Questions numbered with 1. 2. 3. etc.
    - Options with A. B. C. D. etc.
    - Answer on a line starting with "答案" or "Answer"
    - Explanation on a line starting with "解析" or "Explanation"
    """
    questions = []
    lines = content.split("\n")

    current_q = None
    import re

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect new question start
        if current_q is None or (stripped and re.match(r'^\d+[\.、\)]\s*', stripped)):
            if current_q is not None and current_q.get("question"):
                questions.append(current_q)

            if stripped and re.match(r'^\d+[\.、\)]\s*', stripped):
                q_text = re.sub(r'^\d+[\.、\)]\s*', '', stripped)
            else:
                q_text = ""

            current_q = {
                "question": q_text,
                "options": [],
                "answer": "",
                "explanation": "",
                "images": [],
            }
            i += 1
            continue

        if current_q is None:
            i += 1
            continue

        # Detect option lines: A. B. C. D. or A、 B、 C、 D、
        option_match = re.match(r'^([A-Fa-f])[\.\、\)]\s*(.*)', stripped)
        if option_match and current_q is not None:
            current_q["options"].append(option_match.group(2))
            i += 1
            continue

        # Detect answer line
        answer_match = re.match(r'^(?:答案|Answer)[：:]\s*(.*)', stripped)
        if answer_match and current_q is not None:
            current_q["answer"] = answer_match.group(1).strip()
            i += 1
            continue

        # Detect explanation line
        expl_match = re.match(r'^(?:解析|Explanation)[：:]\s*(.*)', stripped)
        if expl_match and current_q is not None:
            current_q["explanation"] = expl_match.group(1).strip()
            i += 1
            continue

        # Detect image reference
        img_match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if img_match and current_q is not None:
            current_q["images"].append(img_match.group(2))
            i += 1
            continue

        # Accumulate text into current field
        if current_q and stripped:
            if current_q["question"] and not current_q["options"]:
                current_q["question"] += " " + stripped
            elif current_q["options"]:
                current_q["options"][-1] += " " + stripped
            elif current_q["answer"]:
                current_q["answer"] += " " + stripped
            elif current_q["explanation"]:
                current_q["explanation"] += " " + stripped

        i += 1

    if current_q is not None and current_q.get("question"):
        questions.append(current_q)

    name = os.path.splitext(filename)[0]
    from LOBN_exam_speech_board_reflex.data.question_bank import QuestionBank
    bank = QuestionBank(name=name, filename=filename, questions=questions)
    return normalize_question_bank(bank)


def image_to_base64(file_path: str) -> str:
    """Convert an image file to base64 data URI."""
    with open(file_path, "rb") as f:
        data = f.read()
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "image/png"
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def get_import_files() -> list:
    """Get list of files in the import directory."""
    ensure_directories()
    files = []
    for fname in os.listdir(IMPORT_DIR):
        fpath = os.path.join(IMPORT_DIR, fname)
        if os.path.isfile(fpath):
            files.append({
                "filename": fname,
                "size": os.path.getsize(fpath),
                "modified": os.path.getmtime(fpath),
            })
    return files


def clean_import_file(filename: str) -> bool:
    """Remove a file from the import directory."""
    fpath = os.path.join(IMPORT_DIR, filename)
    if os.path.exists(fpath):
        os.remove(fpath)
        return True
    return False
