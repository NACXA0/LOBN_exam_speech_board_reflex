# Question bank data models

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Question:
    """Single question model."""
    id: int
    question: str
    options: List[str]
    answer: str
    explanation: str = ""
    images: List[str] = field(default_factory=list)  # base64 image strings or paths
    type: str = "single"  # single / multiple / judge

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Question:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class QuestionBank:
    """Question bank metadata and content."""
    name: str
    filename: str
    description: str = ""
    questions: List[Question] = field(default_factory=list)

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "filename": self.filename,
            "description": self.description,
            "total_questions": len(self.questions),
            "questions": [q.to_dict() for q in self.questions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> QuestionBank:
        questions = [Question.from_dict(q) for q in data.get("questions", [])]
        return cls(
            name=data.get("name", ""),
            filename=data.get("filename", ""),
            description=data.get("description", ""),
            questions=questions,
        )


# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")
QUESTION_BANKS_DIR = os.path.join(ASSETS_DIR, "question_banks")
IMPORT_DIR = os.path.join(DATA_DIR, "import")
TEMP_DIR = os.path.join(DATA_DIR, "temp")


def ensure_directories():
    """Ensure all required directories exist."""
    os.makedirs(QUESTION_BANKS_DIR, exist_ok=True)
    os.makedirs(IMPORT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)


def _count_questions(fpath: str, fname: str) -> int:
    """Count questions in a bank file without full parsing."""
    try:
        if fname.endswith(".json"):
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return len(data.get("questions", []))
            elif isinstance(data, list):
                return len(data)
    except Exception:
        pass
    return 0


def get_all_bank_files() -> List[dict]:
    """Get list of available question bank files."""
    ensure_directories()
    banks = []
    for fname in sorted(os.listdir(QUESTION_BANKS_DIR)):
        if fname.endswith((".json", ".md")):
            fpath = os.path.join(QUESTION_BANKS_DIR, fname)
            bank_info = {
                "filename": fname,
                "name": os.path.splitext(fname)[0],
                "size": os.path.getsize(fpath),
                "modified": os.path.getmtime(fpath),
                "total_questions": _count_questions(fpath, fname),
                "description": "",
            }
            # 读取 JSON 文件中的 description 和 name
            if fname.endswith(".json"):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        bank_info["description"] = data.get("description", "")
                        if data.get("name"):
                            bank_info["name"] = data["name"]
                except Exception:
                    pass
            banks.append(bank_info)
    return banks


def load_question_bank(filename: str) -> Optional[QuestionBank]:
    """Load a question bank from file."""
    ensure_directories()
    fpath = os.path.join(QUESTION_BANKS_DIR, filename)
    if not os.path.exists(fpath):
        return None

    if filename.endswith(".json"):
        return _load_json(fpath, filename)
    elif filename.endswith(".md"):
        return _load_markdown(fpath, filename)
    return None


def save_question_bank(bank: QuestionBank) -> str:
    """Save a question bank to file. Returns the filename."""
    ensure_directories()
    # Use JSON format for storage
    fpath = os.path.join(QUESTION_BANKS_DIR, bank.filename)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(bank.to_dict(), f, ensure_ascii=False, indent=2)
    return bank.filename


def delete_question_bank(filename: str) -> bool:
    """Delete a question bank file."""
    fpath = os.path.join(QUESTION_BANKS_DIR, filename)
    if os.path.exists(fpath):
        os.remove(fpath)
        return True
    return False


def rename_question_bank(old_filename: str, new_name: str) -> bool:
    """Rename a question bank file."""
    fpath = os.path.join(QUESTION_BANKS_DIR, old_filename)
    if not os.path.exists(fpath):
        return False
    new_filename = new_name + ".json"
    new_path = os.path.join(QUESTION_BANKS_DIR, new_filename)
    os.rename(fpath, new_path)
    return True


def _load_json(fpath: str, filename: str) -> QuestionBank:
    """Load question bank from JSON file."""
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return QuestionBank.from_dict({
        **data,
        "filename": filename,
    })


def _load_markdown(fpath: str, filename: str) -> QuestionBank:
    """Load question bank from Markdown file."""
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    return _parse_markdown(content, filename)


def parse_markdown_to_bank(content: str, filename: str = "imported.md") -> QuestionBank:
    """Parse markdown content into a QuestionBank."""
    return _parse_markdown(content, filename)


def _parse_markdown(content: str, filename: str) -> QuestionBank:
    """Parse markdown formatted question bank content."""
    questions = []
    # Split by question markers (lines starting with "## " or numbered patterns)
    lines = content.split("\n")

    # Try to find question blocks
    current_q = None
    current_field = None
    field_data = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect question start - "## " or "### " or "第X题" or "Question X" or numbered
        if (line.startswith("## ") or line.startswith("### ") or
            line.startswith("第") and "题" in line[:6] or
            line.upper().startswith("QUESTION") or
            (line and line[0].isdigit() and "." in line[:5] and not current_q)):

            if current_q is not None:
                questions.append(_build_question(current_q, field_data))

            current_q = {"question": "", "options": [], "answer": "", "explanation": "", "images": []}
            field_data = {}

            # Extract question text
            q_text = line.lstrip("#").strip()
            # Remove "第X题" prefix
            import re
            q_text = re.sub(r'^第[\d一二三四五六七八九十]+题\s*', '', q_text)
            current_q["question"] = q_text
            i += 1
            continue

        # Detect option lines
        if current_q and (line.startswith(("A.", "B.", "C.", "D.", "E.", "F.")) or
                          line.startswith(("a)", "b)", "c)", "d)", "e)", "f)")) or
                          line.startswith(("A、", "B、", "C、", "D、", "E、", "F、"))):
            option_text = re.sub(r'^[A-Fa-f][\.、\)]\s*', '', line)
            current_q["options"].append(option_text)
            i += 1
            continue

        # Detect answer line
        if current_q and (line.startswith("答案：") or line.startswith("答案:") or
                          line.startswith("Answer:") or line.startswith("Answer：")):
            current_q["answer"] = line.split("：")[-1].split(":")[-1].strip()
            i += 1
            continue

        # Detect explanation line
        if current_q and (line.startswith("解析：") or line.startswith("解析:") or
                          line.startswith("解析:") or line.startswith("Explanation:") or line.startswith("Explanation：")):
            current_q["explanation"] = line.split("：")[-1].split(":")[-1].strip()
            i += 1
            continue

        # Detect image reference
        if current_q and line.startswith("![") and "](" in line:
            import re
            img_match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            if img_match:
                current_q["images"].append(img_match.group(2))
            i += 1
            continue

        # Accumulate field text
        if current_q:
            if line and not line.startswith("#"):
                if current_q["question"] and not current_q["options"]:
                    # Still in question text
                    if not current_q["question"].endswith("\n"):
                        current_q["question"] += " " + line
                elif current_q["options"]:
                    # Option continuation
                    current_q["options"][-1] += " " + line
                elif current_q["answer"]:
                    current_q["answer"] += " " + line
                elif current_q["explanation"]:
                    current_q["explanation"] += " " + line

        i += 1

    # Don't forget the last question
    if current_q is not None:
        questions.append(_build_question(current_q, field_data))

    name = os.path.splitext(filename)[0]
    return QuestionBank(name=name, filename=filename, questions=questions)


def _detect_question_type(options: list[str], answer: str) -> str:
    """Detect question type from options and answer."""
    opts = [opt.strip() for opt in options]
    if len(opts) == 2 and opts in (["√", "×"], ["对", "错"], ["正确", "错误"], ["A.正确", "B.错误"]):
        return "judge"
    ans = answer.strip().upper()
    if len(ans) > 1:
        return "multiple"
    return "single"


def _build_question(data: dict, field_data: dict) -> Question:
    """Build a Question from parsed data."""
    options = data.get("options", [])
    answer = data.get("answer", "")
    q_type = data.get("type", _detect_question_type(options, answer))
    return Question(
        id=0,  # Will be assigned later
        question=data.get("question", ""),
        options=options,
        answer=answer,
        explanation=data.get("explanation", ""),
        images=data.get("images", []),
        type=q_type,
    )


def normalize_question_bank(bank: QuestionBank) -> QuestionBank:
    """Assign sequential IDs and clean up data."""
    for i, q in enumerate(bank.questions, 1):
        q.id = i
    return bank
