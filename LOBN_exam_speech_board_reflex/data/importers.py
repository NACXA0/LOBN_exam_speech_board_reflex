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
    IMPORT_DIR,
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
    from LOBN_exam_speech_board_reflex.data.question_bank import Question, QuestionBank as _QB
    import json
    data = json.loads(content)
    raw_items: list[dict] = []
    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict):
        raw_items = data.get("questions", data.get("题库", []))
    else:
        raise ValueError("Invalid JSON structure")

    questions: list[Question] = []
    for item in raw_items:
        options = item.get("options", item.get("选项", []))
        answer = item.get("answer", item.get("答案", ""))
        q_type = item.get("type", item.get("题型", ""))
        if not q_type:
            from LOBN_exam_speech_board_reflex.data.question_bank import _detect_question_type
            q_type = _detect_question_type(options, answer)
        questions.append(Question(
            id=0,
            question=item.get("question", item.get("题干", "")),
            options=options,
            answer=answer,
            explanation=item.get("explanation", item.get("解析", "")),
            images=item.get("images", item.get("图片", [])),
            type=q_type,
        ))

    name = os.path.splitext(filename)[0]
    bank = _QB(name=name, filename=filename, questions=questions)
    return normalize_question_bank(bank)


def import_doc_content(file_path: str, filename: str = "imported.doc") -> QuestionBank:
    """Import question bank from legacy .doc file.
    Tries win32com (Windows + MS Word) first, then falls back to python-docx
    (in case the file is actually a .docx renamed as .doc).
    """
    # Try win32com (Windows COM automation with MS Word installed)
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(file_path))
        content = doc.Content.Text
        doc.Close(False)
        word.Quit()
        pythoncom.CoUninitialize()
        return parse_text_to_bank(content, filename)
    except Exception:
        pass

    # Fallback: try python-docx (works if the file is actually .docx format)
    try:
        return import_docx_content(file_path, filename)
    except Exception:
        raise ValueError(
            "无法读取 .doc 文件。请用 Word 另存为 .docx 格式后重试，"
            "或在安装了 Microsoft Word 的 Windows 环境下使用。"
        )


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

    Supports two layout styles:
    Style A - Inline: answer/explanation follow each question immediately.
    Style B - Separated: answer/explanation are collected at the end of the file,
              in the format "N、答案: [X]" / "解析：...".

    Also handles:
    - Questions without numbers (detected by leading A. option after D.)
    - Category headers like "单选题 共100 题", "判断题", "题目解析"
    - Option formats: A. / A、/ A) with optional spaces
    - True/False questions (A.正确 B.错误)
    """
    from LOBN_exam_speech_board_reflex.data.question_bank import Question, QuestionBank as _QB

    lines = content.split("\n")

    # ------------------------------------------------------------------
    # Pre-scan: locate the "answer section" (lines starting with "N、答案:")
    # and build a map  question_number -> (answer, explanation)
    # ------------------------------------------------------------------
    answer_map: dict[int, dict] = {}  # {num: {"answer": ..., "explanation": ...}}
    answer_section_start: int | None = None
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # Detect answer lines like "1、答案: [D]" or "1、答案：[D]"
        ans_m = re.match(r'^(\d+)[\.、\)]\s*答案\s*[：:]\s*(.*)', stripped)
        if ans_m:
            if answer_section_start is None:
                answer_section_start = i
            q_num = int(ans_m.group(1))
            ans_text = ans_m.group(2).strip()
            # Clean brackets like [D] -> D
            ans_text = re.sub(r'[\[\[【】\]]', '', ans_text).strip()
            entry = answer_map.setdefault(q_num, {"answer": "", "explanation": ""})
            entry["answer"] = ans_text
            # Look for explanation on the next lines
            j = i + 1
            expl_parts: list[str] = []
            while j < len(lines):
                next_s = lines[j].strip()
                expl_m = re.match(r'^(?:解析|Explanation)[：:]\s*(.*)', next_s)
                if expl_m:
                    expl_parts.append(expl_m.group(1).strip())
                    j += 1
                    continue
                # Continuation of explanation (indented or short non-question line)
                if next_s and not re.match(r'^\d+[\.、\)]\s*答案', next_s) and (
                    next_s.startswith(' ') or next_s.startswith('\t') or expl_parts
                ):
                    # Stop if we hit a new answer line or a new question
                    if re.match(r'^\d+[\.、\)]\s*', next_s) and not re.match(r'^\d+[\.、\)]\s*答案', next_s):
                        break
                    expl_parts.append(next_s)
                    j += 1
                    continue
                break
            if expl_parts:
                entry["explanation"] = ' '.join(expl_parts)
            i = j
            continue
        i += 1

    # ------------------------------------------------------------------
    # Main pass: parse questions and options
    # Skip lines that belong to the answer section
    # ------------------------------------------------------------------
    questions: list[Question] = []
    current_q: dict | None = None
    current_q_num: int | None = None  # track the question number for answer backfill

    # Patterns to skip (category headers, etc.)
    skip_patterns = [
        re.compile(r'^题目解析'),
        re.compile(r'^共\d+\s*题'),
    ]
    type_patterns = [
        (re.compile(r'^单选题'), "single"),
        (re.compile(r'^多选题'), "multiple"),
        (re.compile(r'^判断题'), "judge"),
    ]

    def _is_skip_line(s: str) -> bool:
        for pat in skip_patterns:
            if pat.match(s):
                return True
        return False

    def _detect_section_type(s: str) -> str | None:
        for pat, q_type in type_patterns:
            if pat.match(s):
                return q_type
        return None

    current_section_type = "single"

    def _save_current():
        nonlocal current_q, current_q_num
        if current_q and current_q.get("question"):
            q_text = current_q["question"].strip()
            if q_text:
                # Backfill answer from answer_map if not already set inline
                if not current_q["answer"] and current_q_num and current_q_num in answer_map:
                    current_q["answer"] = answer_map[current_q_num]["answer"]
                    current_q["explanation"] = answer_map[current_q_num]["explanation"]
                q_type = current_q.get("type", "")
                if not q_type:
                    from LOBN_exam_speech_board_reflex.data.question_bank import _detect_question_type
                    q_type = _detect_question_type(current_q.get("options", []), current_q.get("answer", ""))
                questions.append(Question(
                    id=0,
                    question=q_text,
                    options=current_q.get("options", []),
                    answer=current_q.get("answer", ""),
                    explanation=current_q.get("explanation", ""),
                    images=current_q.get("images", []),
                    type=q_type,
                ))
        current_q = None
        current_q_num = None

    i = 0
    while i < len(lines):
        # Skip lines in the answer section
        if answer_section_start is not None and i >= answer_section_start:
            break

        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Detect section type from category headers
        section_type = _detect_section_type(stripped)
        if section_type:
            current_section_type = section_type
            i += 1
            continue

        # Skip other headers
        if _is_skip_line(stripped):
            i += 1
            continue

        # Skip title lines (first line typically like "消防设施操作员...模拟试题二")
        # We detect this as: a line before any question that doesn't look like a question or option
        if current_q is None and not re.match(r'^\d+[\.、\)]', stripped) and not re.match(r'^[A-Fa-f][\.、\)]', stripped):
            i += 1
            continue

        # ---- Detect answer line (inline style, e.g. "答案：D") ----
        answer_match = re.match(r'^(?:答案|Answer)[：:]\s*(.*)', stripped)
        if answer_match and current_q is not None:
            current_q["answer"] = answer_match.group(1).strip()
            i += 1
            continue

        # ---- Detect explanation line (inline style) ----
        expl_match = re.match(r'^(?:解析|Explanation)[：:]\s*(.*)', stripped)
        if expl_match and current_q is not None:
            current_q["explanation"] = expl_match.group(1).strip()
            i += 1
            continue

        # ---- Detect option lines: A. / A、/ A) ----
        option_match = re.match(r'^([A-Fa-f])[\.\.、\)]\s*(.*)', stripped)
        if option_match and current_q is not None:
            opt_letter = option_match.group(1).upper()
            opt_text = option_match.group(2).strip()

            # Heuristic: if option A appears but current question already has
            # 4 (or 2 for T/F) options, this likely starts a NEW question
            # whose number is missing from the source text.
            if opt_letter == 'A' and current_q.get("options"):
                opts_count = len(current_q["options"])
                if opts_count >= 2:  # already has a complete set of options
                    _save_current()
                    current_q = {
                        "question": "",
                        "options": [],
                        "answer": "",
                        "explanation": "",
                        "images": [],
                        "type": current_section_type,
                    }
                    current_q_num = None

            current_q["options"].append(opt_text)
            i += 1
            continue

        # ---- Detect new question: "N、" or "N." or "N)" ----
        q_match = re.match(r'^(\d+)[\.、\)]\s*(.*)', stripped)
        if q_match:
            # But skip if it looks like an answer line "N、答案:"
            if re.match(r'^\d+[\.、\)]\s*答案', stripped):
                i += 1
                continue
            _save_current()
            q_num = int(q_match.group(1))
            q_text = q_match.group(2).strip()
            current_q = {
                "question": q_text,
                "options": [],
                "answer": "",
                "explanation": "",
                "images": [],
                "type": current_section_type,
            }
            current_q_num = q_num
            i += 1
            continue

        # ---- Detect image reference ----
        img_match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if img_match and current_q is not None:
            current_q["images"].append(img_match.group(2))
            i += 1
            continue

        # ---- Accumulate text into current field ----
        if current_q and stripped:
            # Heuristic: if the current question already has a complete set
            # of options (>= 4 for choice, or >= 2 for T/F), and we encounter
            # a non-option, non-question, non-answer line, it is likely the
            # start of a new question whose number is missing from the text.
            # We treat it as a new question's question text.
            if current_q.get("options") and len(current_q["options"]) >= 2:
                _save_current()
                current_q = {
                    "question": stripped,
                    "options": [],
                    "answer": "",
                    "explanation": "",
                    "images": [],
                    "type": current_section_type,
                }
                current_q_num = None
            elif not current_q["options"]:
                # Still in question text
                current_q["question"] += " " + stripped
            else:
                # Append to last option (multi-line option)
                current_q["options"][-1] += " " + stripped

        i += 1

    # Save the last question
    _save_current()

    # ------------------------------------------------------------------
    # Final backfill: for any questions that still have no answer but
    # exist in the answer_map, try matching by position (sequential)
    # ------------------------------------------------------------------
    if answer_map:
        # Build a set of question numbers we already backfilled
        backfilled_nums = set()
        for q in questions:
            # Try to find the original question number from the text
            # (stored during parsing via current_q_num -> no longer accessible)
            pass

        # Alternative: match by sequential position
        # Sort answer_map by number, sort questions by their order
        sorted_answer_nums = sorted(answer_map.keys())
        for idx, q in enumerate(questions):
            if not q.answer and idx < len(sorted_answer_nums):
                num = sorted_answer_nums[idx]
                q.answer = answer_map[num]["answer"]
                q.explanation = answer_map[num]["explanation"]

    name = os.path.splitext(filename)[0]
    bank = _QB(name=name, filename=filename, questions=questions)
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
