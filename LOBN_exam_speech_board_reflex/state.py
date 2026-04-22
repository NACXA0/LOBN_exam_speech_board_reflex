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
# AdminState moved to the bottom of this file to avoid circular imports


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

    @rx.event(background=True)
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

    @rx.event
    def load_bank(self, filename: str):
        """Load a question bank and start the quiz."""
        bank = load_question_bank(filename)
        if bank:
            self.current_bank = bank.to_dict()
            self.current_bank_filename = filename
            self.current_index = 0
            self.selected_option = -1
            self.show_explanation = False
        else:
            raise Exception(f"Failed to load bank: {filename}")

    @rx.event
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
                if question_id in self.answer_history:
                    del self.answer_history[question_id]

    @rx.event
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
                if question_id in self.answer_history:
                    del self.answer_history[question_id]

    @rx.event
    def select_option(self, index: int):
        """Handle option selection."""
        self.selected_option = index
        self.show_explanation = True
        
        # Record answer for statistics
        questions = self.current_bank.get("questions", [])
        if 0 <= self.current_index < len(questions):
            question_id = questions[self.current_index].get("id", self.current_index)
            self.answer_history[question_id] = {
                "selected": index,
                "correct": False,  # Will be updated after checking
            }

    @rx.event
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
                    self.answer_history[question.get("id", self.current_index)]["correct"] = (i == selected_option)
                    break
        
        # Reset selection after checking
        self.selected_option = -1

    @rx.event
    def reset_quiz(self):
        """Reset current quiz state."""
        self.current_index = 0
        self.selected_option = -1
        self.show_explanation = False
        self.answer_history = {}

    @rx.var
    def current_question(self) -> dict:
        """Get current question data for rendering."""
        questions = self.current_bank.get("questions", [])
        if 0 <= self.current_index < len(questions):
            return questions[self.current_index]
        return {}

    @rx.var
    def current_bank_name(self) -> str:
        """Get current bank name for rendering."""
        return self.current_bank.get("name", "未命名题库")

    @rx.var
    def total_questions(self) -> int:
        """Get total question count for rendering."""
        return self.current_bank.get("total_questions", 0)

    @rx.var
    def current_question_text(self) -> str:
        """Get current question text."""
        return self.current_question.get("question", "")

    @rx.var
    def current_question_images(self) -> list[str]:
        """Get current question images."""
        return self.current_question.get("images", [])

    @rx.var
    def current_question_options(self) -> list[str]:
        """Get current question options."""
        return self.current_question.get("options", [])

    @rx.var
    def current_question_answer(self) -> str:
        """Get current question answer (uppercase and stripped)."""
        return self.current_question.get("answer", "").strip().upper()

    @rx.var
    def current_question_explanation(self) -> str:
        """Get current question explanation."""
        return self.current_question.get("explanation", "")

    @rx.var
    def current_question_id(self) -> str:
        """Get current question ID or index."""
        return str(self.current_question.get("id", self.current_index + 1))

    @rx.var
    def option_letters(self) -> list[str]:
        """Get list of option letters (A, B, C, D...) for current question."""
        num_options = len(self.current_question.get("options", []))
        return [chr(65 + i) for i in range(num_options)]  # A, B, C, D...

    @rx.var
    def options_with_letters(self) -> list[dict]:
        """Get options with their corresponding letters."""
        options = self.current_question.get("options", [])
        result = []
        for i, opt in enumerate(options):
            result.append({
                "letter": chr(65 + i),
                "text": opt,
                "index": i
            })
        return result

    @rx.var
    def answer_statistics(self) -> dict[str, str | int | bool | float]:
        """Get answer statistics for current quiz."""
        total = len(self.answer_history)
        correct = sum(1 for v in self.answer_history.values() if v.get("correct", False))
        incorrect = total - correct
        accuracy_value = correct/total*100 if total > 0 else 0
        return {
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": f"{accuracy_value:.1f}%" if total > 0 else "0%",
            "accuracy_value": accuracy_value,  # Numeric value for comparison
            "is_good": accuracy_value >= 70,  # Boolean for color scheme
        }

    # ---- Upload / Import handlers ----
    @rx.event
    async def handle_text_upload(self, text: str, filename: str = "imported.txt"):
        """Process text-based upload."""
        get_AdminState = self.get_state(AdminState)
        try:
            self.upload_status = "正在解析..."
            bank = import_text_content(text, filename)
            # 提取 description（从文件头或作为单独字段）
            desc = getattr(get_AdminState, 'bank_description', '').strip() if hasattr(get_AdminState, 'bank_description') else ""
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

    @rx.event
    async def handle_file_upload(self, files: list[rx.UploadFile]):
        """Handle file upload from the file upload tab."""
        get_AdminState = self.get_state(AdminState)
        if not files:
            self.upload_status = "未选择文件"
            return

        file = files[0]
        try:
            self.upload_status = "正在解析..."
            content = await file.read()
            filename = file.filename or "uploaded.txt"

            if filename.endswith(".docx"):
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                bank = import_docx_content(tmp_path, filename)
                os.unlink(tmp_path)
            elif filename.endswith(".json"):
                text = content.decode("utf-8")
                bank = import_json_content(text, filename)
            elif filename.endswith(".md"):
                text = content.decode("utf-8")
                bank = import_markdown_content(text, filename)
            else:
                text = content.decode("utf-8")
                bank = parse_text_to_bank(text, filename)

            desc = getattr(get_AdminState, 'bank_description', '').strip() if hasattr(get_AdminState, 'bank_description') else ""
            if desc:
                bank_to_dict = bank.to_dict()
                if "description" not in bank_to_dict:
                    bank_to_dict["description"] = desc
                    from LOBN_exam_speech_board_reflex.data.question_bank import QuestionBank
                    bank = QuestionBank.from_dict(bank_to_dict)

            self.preview_bank = bank.to_dict()
            self.uploaded_file = {
                "filename": filename,
                "size": len(content),
            }
            self.upload_status = "解析完成，请确认内容"
        except Exception as e:
            self.upload_status = f"解析失败：{str(e)}"
            self.uploaded_file = None

    @rx.event
    def refresh_import_files(self):
        """Refresh the import files list."""
        self.import_files = get_import_files()

    @rx.event
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

    @rx.event
    def delete_bank(self, filename: str):
        """Delete a question bank."""
        if delete_question_bank(filename):
            self.bank_list = get_all_bank_files()

    @rx.event
    def rename_bank(self, old_filename: str, new_name: str):
        """Rename a question bank."""
        if rename_question_bank(old_filename, new_name):
            self.bank_list = get_all_bank_files()

    @rx.event
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


class AdminState(AppState):
    """State for the admin page. Inherits AppState for shared fields (preview_bank, upload_status, etc.)."""
    upload_tab: str = "text"
    text_content: str = ""
    md_content: str = ""
    json_content: str = ""
    new_bank_name: str = ""
    bank_description: str = ""  # 题库描述
    rename_filename: str = ""
    rename_new_name: str = ""
    show_delete_confirm: str = ""
    preview_mode: bool = False
    current_action_bank_filename: str = ""  # 当前操作的题库文件名
    current_action_type: str = ""  # 当前操作类型：rename, edit_desc, delete

    @staticmethod
    def _format_time(timestamp) -> str:
        """Format timestamp to readable date string."""
        if not timestamp:
            return "未知"
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

    # ---- Computed vars for proper typing in rx.foreach ----

    @rx.var
    def preview_questions(self) -> list[dict]:
        """Get preview questions list with explicit typing for rx.foreach."""
        questions = self.preview_bank.get("questions", [])
        return questions if isinstance(questions, list) else []

    @rx.var
    def preview_questions_formatted(self) -> list[dict]:
        """Get preview questions with formatted display text."""
        questions = self.preview_bank.get("questions", [])
        if not isinstance(questions, list):
            return []
        result = []
        for q in questions:
            q_copy = dict(q)
            q_id = q.get("id", "?")
            question_text = q.get("question", "")
            q_copy["display_brief"] = f"第{q_id}题：{question_text[:50]}"
            q_copy["display_id"] = f"第{q_id}题"
            q_copy["display_question"] = question_text
            result.append(q_copy)
        return result

    @rx.var
    def preview_questions_brief(self) -> list[dict]:
        """Get first 5 preview questions with formatted display text."""
        return self.preview_questions_formatted[:5]

    @rx.var
    def preview_total_questions(self) -> int:
        """Get total questions count from preview bank."""
        return self.preview_bank.get("total_questions", 0)

    @rx.var
    def has_preview(self) -> bool:
        """Whether there is a preview bank loaded."""
        return bool(self.preview_bank)

    @rx.var
    def import_files_list(self) -> list[dict]:
        """Get import files list with explicit typing for rx.foreach."""
        return self.import_files if isinstance(self.import_files, list) else []

    @rx.var
    def bank_list_items(self) -> list[dict]:
        """Get bank list with explicit typing for rx.foreach."""
        return self.bank_list if isinstance(self.bank_list, list) else []

    @rx.var
    def bank_list_formatted(self) -> list[dict]:
        """Get bank list with formatted fields for display."""
        banks = self.bank_list if isinstance(self.bank_list, list) else []
        result = []
        for bank in banks:
            bank_copy = dict(bank)
            description = bank.get("description", "")
            bank_copy["display_description"] = f"{description[:50]}{'...' if len(description) > 50 else ''}"
            # 格式化时间
            modified_timestamp = bank.get("modified", 0)
            if modified_timestamp:
                from datetime import datetime
                dt = datetime.fromtimestamp(modified_timestamp)
                bank_copy["display_modified"] = dt.strftime("%Y-%m-%d %H:%M")
            else:
                bank_copy["display_modified"] = "未知"
            result.append(bank_copy)
        return result

    @rx.var
    def uploaded_file_size_kb(self) -> str:
        """Get uploaded file size in KB as formatted string."""
        if self.uploaded_file:
            size_bytes = self.uploaded_file.get("size", 0)
            return f"{size_bytes / 1024:.1f} KB"
        return "0 KB"

    @rx.var
    def import_files_with_size(self) -> list[dict]:
        """Get import files list with formatted size."""
        files = self.import_files if isinstance(self.import_files, list) else []
        result = []
        for f in files:
            file_copy = dict(f)
            size_bytes = f.get("size", 0)
            file_copy["size_kb"] = f"{size_bytes / 1024:.1f} KB"
            result.append(file_copy)
        return result

    @rx.event
    def set_upload_tab(self, value: str):
        """Set the active upload tab."""
        self.upload_tab = value

    @rx.event
    def set_text_content(self, text: str):
        """Set text content state."""
        AdminState.text_content = text

    @rx.event
    def set_rename_new_name(self, name: str):
        """Set rename new name state."""
        AdminState.rename_new_name = name

    @rx.event
    def confirm_preview(self):
        """Confirm and save the previewed bank."""
        if self.preview_bank:
            bank = QuestionBank.from_dict(self.preview_bank)
            if self.new_bank_name:
                bank.name = self.new_bank_name
                bank.filename = f"{self.new_bank_name}.json"
            save_question_bank(bank)
            self.upload_status = "题库保存成功"
            self.preview_bank = {}
            self.text_content = ""
            self.new_bank_name = ""
            self.bank_description = ""
            self.uploaded_file = None
            # 刷新bank list
            self.bank_list = get_all_bank_files()

    @rx.event
    def discard_preview(self):
        """Discard the preview and reset form."""
        self.preview_bank = {}
        self.upload_status = ""
        self.uploaded_file = None

    @rx.event
    def set_show_delete_confirm(self, value: str):
        """Set the delete confirm dialog."""
        AdminState.show_delete_confirm = value

    @rx.event
    def open_action_dialog(self, action_type: str, filename: str):
        """Open action dialog for a specific bank."""
        AdminState.current_action_type = action_type
        AdminState.current_action_bank_filename = filename
        AdminState.show_delete_confirm = f"{action_type}:{filename}"

    @rx.event
    def close_action_dialog(self):
        """Close action dialog."""
        AdminState.current_action_type = ""
        AdminState.current_action_bank_filename = ""
        AdminState.show_delete_confirm = ""

    @rx.event
    def set_bank_description(self, value: str):
        """Set bank description."""
        AdminState.bank_description = value

    @rx.event
    def set_new_bank_name(self, value: str):
        """Set new bank name."""
        AdminState.new_bank_name = value

    @rx.event
    def clean_import_file(self, filename: str):
        """Clean an import file."""
        clean_import_file(filename)
        # Refresh import files list
        self.refresh_import_files()
