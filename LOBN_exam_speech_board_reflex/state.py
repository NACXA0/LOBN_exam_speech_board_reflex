# Application state management

from __future__ import annotations

import os
import json
import time
from typing import List, Optional

import reflex as rx

from LOBN_exam_speech_board_reflex.data.question_bank import (
    QuestionBank,
    Question,
    load_question_bank,
    save_question_bank,
    delete_question_bank,
    rename_question_bank,
    get_all_bank_files,
    ensure_directories,
)
from LOBN_exam_speech_board_reflex.data.importers import (
    import_text_content,
    import_markdown_content,
    import_json_content,
    import_docx_content,
    parse_text_to_bank,
    get_import_files,
    clean_import_file,
    image_to_base64,
)


class AppState(rx.State):
    """Base state shared across all pages."""

    # Current question bank
    current_bank: dict = {}
    current_bank_filename: str = ""

    # Current question index
    current_index: int = 0

    # UI state
    selected_option: int = -1
    show_explanation: bool = False
    is_painting: bool = False
    painting_mode: str = "pen"  # pen, eraser

    # Answer history for statistics
    answer_history: dict = {}  # {question_id: {"selected": option_idx, "correct": bool}}

    # Bank list for wellcome page
    bank_list: list[dict] = []

    # Upload state
    upload_progress: int = 0
    upload_status: str = ""
    preview_bank: dict = {}

    # File upload state
    uploaded_file: Optional[dict] = None

    # Import files list
    import_files: list[dict] = []

    async def initialize(self):
        """Load available question banks on app start."""
        raw_banks = get_all_bank_files()
        formatted = []
        for b in raw_banks:
            from datetime import datetime
            dt = datetime.fromtimestamp(b.get("modified", 0))
            formatted.append({
                "filename": b["filename"],
                "name": b.get("name", "未命名题库"),
                "size_kb": f"{b.get('size', 0) / 1024:.1f}",
                "modified_str": dt.strftime("%Y-%m-%d %H:%M"),
            })
        self.bank_list = formatted

    def load_bank(self, filename: str):
        """Load a question bank and start the quiz."""
        bank = load_question_bank(filename)
        if bank:
            self.current_bank = bank.to_dict()
            self.current_bank_filename = filename
            self.current_index = 0
            self.selected_option = -1
            self.show_explanation = False
            self.is_painting = False
        else:
            raise Exception(f"Failed to load bank: {filename}")

    def next_question(self):
        """Go to next question."""
        total = self.current_bank.get("total_questions", 0)
        if self.current_index < total - 1:
            self.current_index += 1
            self.selected_option = -1
            self.show_explanation = False
            # Reset answer history for current question
            questions = self.current_bank.get("questions", [])
            if 0 <= self.current_index < len(questions):
                question_id = questions[self.current_index].get("id", self.current_index)
                if question_id in answer_history:
                    del answer_history[question_id]

    def prev_question(self):
        """Go to previous question."""
        if self.current_index > 0:
            self.current_index -= 1
            self.selected_option = -1
            self.show_explanation = False
            # Reset answer history for current question
            questions = self.current_bank.get("questions", [])
            if 0 <= self.current_index < len(questions):
                question_id = questions[self.current_index].get("id", self.current_index)
                if question_id in answer_history:
                    del answer_history[question_id]

    def select_option(self, index: int):
        """Handle option selection."""
        self.selected_option = index
        self.show_explanation = True
        
        # Record answer for statistics
        questions = self.current_bank.get("questions", [])
        if 0 <= self.current_index < len(questions):
            question_id = questions[self.current_index].get("id", self.current_index)
            answer_history[question_id] = {
                "selected": index,
                "correct": False,  # Will be updated after checking
            }

    def check_answer(self):
        """Check if the selected answer is correct."""
        questions = self.current_bank.get("questions", [])
        if 0 <= self.current_index < len(questions):
            question = questions[self.current_index]
            correct_answer = question.get("answer", "")
            selected_option = self.selected_option
            
            # Find which option matches the correct answer
            options = question.get("options", [])
            for i, opt in enumerate(options):
                if opt == correct_answer or opt.lower() == correct_answer.lower():
                    answer_history[question.get("id", self.current_index)]["correct"] = (i == selected_option)
                    break
        
        # Reset selection after checking
        self.selected_option = -1

    def toggle_painting(self):
        """Toggle painting mode."""
        self.is_painting = not self.is_painting
        if self.is_painting:
            self.show_explanation = False
            self.selected_option = -1
            self.painting_mode = "pen"  # 默认画笔模式

    def toggle_erase(self):
        """Switch to eraser mode."""
        if self.is_painting:
            self.painting_mode = "eraser"

    def reset_quiz(self):
        """Reset current quiz state."""
        self.current_index = 0
        self.selected_option = -1
        self.show_explanation = False
        self.is_painting = False
        self.answer_history = {}

    def get_current_question(self) -> Optional[dict]:
        """Get current question data."""
        questions = self.current_bank.get("questions", [])
        if 0 <= self.current_index < len(questions):
            return questions[self.current_index]
        return None

    def get_current_bank_name(self) -> str:
        """Get current bank name."""
        return self.current_bank.get("name", "")

    def get_answer_statistics(self) -> dict:
        """Get answer statistics for current quiz."""
        total = len(answer_history)
        correct = sum(1 for v in answer_history.values() if v.get("correct", False))
        incorrect = total - correct
        return {
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": f"{correct/total*100:.1f}%" if total > 0 else "0%",
        }

    # ---- Upload / Import handlers ----

    async def handle_text_upload(self, text: str, filename: str = "imported.txt"):
        """Process text-based upload."""
        try:
            self.upload_status = "正在解析..."
            bank = import_text_content(text, filename)
            # 提取 description（从文件头或作为单独字段）
            desc = getattr(AdminState, 'bank_description', '').strip() if hasattr(AdminState, 'bank_description') else ""
            if desc:
                # 更新 preview_bank 中的 description
                if "description" not in bank.to_dict():
                    bank_to_dict = bank.to_dict()
                    bank_to_dict["description"] = desc
                    from LOBN_exam_speech_board_reflex.data.question_bank import QuestionBank
                    bank = QuestionBank.from_dict(bank_to_dict)
            self.preview_bank = bank.to_dict()
            self.upload_status = "解析完成，请确认内容"
        except Exception as e:
            self.upload_status = f"解析失败：{str(e)}"
        finally:
            self.upload_progress = 0

    def refresh_import_files(self):
        """Refresh the import files list."""
        self.import_files = get_import_files()

    def process_import_file(self, filename: str):
        """Process a file from the import directory."""
        from LOBN_exam_speech_board_reflex.data.question_bank import IMPORT_DIR
        fpath = os.path.join(IMPORT_DIR, filename)
        try:
            if filename.endswith(".docx"):
                bank = import_docx_content(fpath, filename)
            elif filename.endswith(".json"):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                bank = import_json_content(content, filename)
            else:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                bank = parse_text_to_bank(content, filename)

            bank.filename = bank.name + ".json"
            save_question_bank(bank)
            clean_import_file(filename)
            self.refresh_import_files()
            self.upload_status = f"文件 '{filename}' 处理成功"
        except Exception as e:
            self.upload_status = f"处理失败: {str(e)}"

    def delete_bank(self, filename: str):
        """Delete a question bank."""
        if delete_question_bank(filename):
            self.bank_list = get_all_bank_files()

    def rename_bank(self, old_filename: str, new_name: str):
        """Rename a question bank."""
        if rename_question_bank(old_filename, new_name):
            self.bank_list = get_all_bank_files()

    def save_bank_description(self, filename: str, description: str) -> bool:
        """Save description for a question bank."""
        try:
            from LOBN_exam_speech_board_reflex.data.question_bank import QUESTION_BANKS_DIR
            fpath = os.path.join(QUESTION_BANKS_DIR, filename)
            if not os.path.exists(fpath):
                return False
            
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["description"] = description
            from LOBN_exam_speech_board_reflex.data.question_bank import save_question_bank
            bank = QuestionBank.from_dict(data)
            new_filename = save_question_bank(bank)
            
            # 更新 bank_list
            self.bank_list = get_all_bank_files()
            return True
        except Exception as e:
            print(f"保存描述失败：{e}")
            return False
