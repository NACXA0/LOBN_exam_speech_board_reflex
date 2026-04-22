# 后台管理页面

import reflex as rx

class AdminState(rx.State):
    """State for the admin page."""
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

    @staticmethod
    def _format_time(timestamp) -> str:
        """Format timestamp to readable date string."""
        if not timestamp:
            return "未知"
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

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
        from LOBN_exam_speech_board_reflex.data.question_bank import QuestionBank, save_question_bank
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
            # 刷新bank list
            self.bank_list = __import__("LOBN_exam_speech_board_reflex.data.question_bank", fromlist=["get_all_bank_files"]).get_all_bank_files()

    @rx.event
    def discard_preview(self):
        """Discard the preview and reset form."""
        self.preview_bank = {}
        self.upload_status = ""

    @rx.event
    def set_show_delete_confirm(self, value: str):
        """Set the delete confirm dialog."""
        AdminState.show_delete_confirm = value

    @rx.event
    def set_bank_description(self, value: str):
        """Set bank description."""
        AdminState.bank_description = value

    @rx.event
    def clean_import_file(self, filename: str):
        """Clean an import file."""
        from LOBN_exam_speech_board_reflex.data.importers import clean_import_file
        clean_import_file(filename)
        # Refresh import files list
        self.refresh_import_files()


def admin() -> rx.Component:
    """后台管理页面 - 题库上传与管理."""
    return rx.container(
        rx.flex(
            rx.heading("后台管理", size="7", weight="bold", color="var(--gray-12)"),
            rx.text("题库上传与管理", size="3", color="var(--gray-9)"),
            direction="column",
            align="center",
            width="100%",
            padding_y="4",
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("在线上传", value="text", padding_x="6"),
                rx.tabs.trigger("文件上传", value="file"),
                rx.tabs.trigger("离线上传", value="offline"),
                rx.tabs.trigger("题库管理", value="manage"),
            ),
            # Tab 1: Online upload (text input)
            rx.tabs.content(
                rx.cond(
                    AdminState.preview_bank != {},
                    rx.flex(
                        # Preview mode
                        rx.card(
                            rx.flex(
                                rx.text("预览", size="4", weight="bold"),
                                rx.text(
                                    f"{AdminState.preview_bank.get('total_questions', 0)} 道题",
                                    size="3",
                                    color="var(--gray-9)",
                                ),
                                spacing="3",
                            ),
                            rx.divider(),
                            rx.foreach(
                                AdminState.preview_bank.get("questions", []),
                                lambda q: rx.flex(
                                    rx.badge(
                                        rx.text(f"第{q.get('id', '?')}题", size="2"),
                                        size="1",
                                        color_scheme="gray",
                                        variant="outline",
                                    ),
                                    rx.text(
                                        q.get("question", ""),
                                        size="3",
                                        color="var(--gray-11)",
                                        line_height="1.6",
                                    ),
                                    spacing="2",
                                ),
                            ),
                            width="100%",
                            size="4",
                            variant="surface",
                        ),
                        rx.cond(
                            AdminState.preview_bank.get("total_questions", 0) > 5,
                            rx.text(
                                f"... 共 {AdminState.preview_bank.get('total_questions', 0)} 道题",
                                size="2",
                                color="var(--gray-8)",
                                style={"fontStyle": "italic"},
                            ),
                        ),
                        direction="column",
                        spacing="3",
                    ),
                ),
                rx.cond(
                    AdminState.preview_bank == {},
                    # Edit mode
                    rx.flex(
                        rx.text_field(
                            placeholder="输入题库名称",
                            value=AdminState.new_bank_name,
                            on_change=AdminState.new_bank_name.__set__,
                            width="100%",
                            size="3",
                            variant="outlined",
                            _placeholder={"color": "var(--gray-7)"},
                        ),
                        rx.text_field(
                            placeholder="题库描述（可选）",
                            value=AdminState.bank_description,
                            on_change=AdminState.bank_description.__set__,
                            width="100%",
                            size="3",
                            variant="outlined",
                            _placeholder={"color": "var(--gray-7)"},
                        ),
                        rx.text_area(
                            placeholder="在此输入题库内容...\n\n支持格式：\n1. 题目编号\n2. 选项 A. B. C. D.\n3. 答案：\n4. 解析：",
                            value=AdminState.text_content,
                            on_change=AdminState.text_content.__set__,
                            width="100%",
                            height="400px",
                            size="4",
                            variant="outlined",
                            font_family="monospace",
                            _placeholder={"color": "var(--gray-7)"},
                        ),
                        rx.flex(
                            rx.button(
                                rx.icon("eye", size=16),
                                "预览",
                                size="3",
                                variant="outline",
                                on_click=AdminState.handle_text_upload(
                                    AdminState.text_content,
                                    AdminState.new_bank_name or "untitled.txt",
                                ),
                            ),
                            rx.button(
                                rx.icon("save", size=16),
                                "保存",
                                size="3",
                                color_scheme="green",
                                variant="solid",
                                on_click=AdminState.confirm_preview,
                                disabled=AdminState.preview_bank == {},
                            ),
                            rx.button(
                                rx.icon("x", size=16),
                                "取消",
                                size="3",
                                variant="outline",
                                on_click=AdminState.discard_preview,
                            ),
                            spacing="3",
                        ),
                        rx.cond(
                            AdminState.upload_status != "",
                            rx.toast(
                                AdminState.upload_status,
                                position="bottom",
                                color_scheme="blue" if "成功" in AdminState.upload_status else "red",
                            ),
                        ),
                        direction="column",
                        spacing="4",
                        width="100%",
                        max_width="900px",
                    ),
                ),
                value="text",
            ),
            rx.text_area(
                placeholder="在此输入题库内容...\n\n支持格式：\n1. 题目编号\n2. 选项 A. B. C. D.\n3. 答案：\n4. 解析：",
                value=AdminState.text_content,
                on_change=AdminState.set_text_content,
                width="100%",
                height="400px",
                size="2",
                variant="classic",
                font_family="monospace",
                _placeholder={"color": "var(--gray-7)"},
            ),
            rx.flex(
                rx.button(
                    rx.icon("eye", size=16),
                    "预览",
                    size="3",
                    variant="outline",
                    on_click=AdminState.handle_text_upload(
                        AdminState.text_content,
                        AdminState.new_bank_name or "untitled.txt",
                    ),
                ),
                rx.button(
                    rx.icon("save", size=16),
                    "保存",
                    size="3",
                    color_scheme="green",
                    variant="solid",
                    on_click=AdminState.confirm_preview,
                    disabled=AdminState.preview_bank == {},
                ),
                rx.button(
                    rx.icon("x", size=16),
                    "取消",
                    size="3",
                    variant="outline",
                    on_click=AdminState.discard_preview,
                ),
                spacing="3",
            ),
            rx.cond(
                AdminState.upload_status != "",
                rx.toast(
                    AdminState.upload_status,
                    position="bottom",
                    color_scheme="blue" if "成功" in AdminState.upload_status else "red",
                ),
            ),
            rx.cond(
                AdminState.preview_bank != {},
                rx.card(
                    rx.flex(
                        rx.flex(
                            rx.text("预览", size="4", weight="bold"),
                            rx.text(
                                f"{AdminState.preview_bank.get('total_questions', 0)} 道题",
                                size="3",
                                color="var(--gray-9)",
                            ),
                            spacing="3",
                        ),
                        rx.divider(),
                        rx.foreach(
                            AdminState.preview_bank.get("questions", [])[:5],
                            lambda questions: rx.flex(
                                rx.text(
                                    f"第{questions.get('id', '?')}题: {questions.get('question', '')[:50]}{rx.cond(questions.get('question', '').length() > 50, '...', '')}",
                                    size="2",
                                    color="var(--gray-11)",
                                ),
                            ),
                        ),
                        rx.cond(
                            AdminState.preview_bank.get("total_questions", 0) > 5,
                            rx.text(
                                f"... 共 {AdminState.preview_bank.get('total_questions', 0)} 道题",
                                size="2",
                                color="var(--gray-8)",
                                style={"fontStyle": "italic"},
                            ),
                        ),
                        direction="column",
                        spacing="3",
                    ),
                    width="100%",
                    size="3",
                    variant="surface",
                    border_left="4px solid var(--green-6)",
                ),
            ),
        # Tab 2: File upload
        rx.tabs.content(
            rx.flex(
                rx.cond(
                    AdminState.uploaded_file,
                    rx.card(
                        rx.flex(
                            rx.icon("file-check", size=48, color="var(--green-9)"),
                            rx.text(AdminState.uploaded_file.filename, size="3", weight="medium"),
                            rx.text(f"{AdminState.uploaded_file.size / 1024:.1f} KB", size="2", color="var(--gray-8)"),
                            spacing="2",
                        ),
                        width="100%",
                        size="3",
                        variant="surface",
                    ),
                ),
                rx.cond(
                    not AdminState.uploaded_file,
                    rx.card(
                        rx.flex(
                            rx.icon("upload-cloud", size=48, color="var(--gray-7)"),
                            rx.text("点击或拖拽文件到此处", size="3", color="var(--gray-9)"),
                            rx.text("支持 .txt, .md, .docx 格式", size="2", color="var(--gray-7)"),
                            direction="column",
                            align="center",
                            spacing="3",
                        ),
                        width="100%",
                        size="3",
                        variant="surface",
                        border="2px dashed var(--gray-5)",
                    ),
                ),
                rx.cond(
                    AdminState.upload_status != "",
                    rx.toast(
                        AdminState.upload_status,
                        position="bottom",
                        color_scheme=rx.cond(AdminState.upload_status.contains("成功"), "blue", "red"),
                    )
                ),
                rx.cond(
                    AdminState.preview_bank != {},
                    rx.card(
                        rx.flex(
                            rx.text("预览", size="4", weight="bold"),
                            rx.divider(),
                            rx.foreach(
                                AdminState.preview_bank.get("questions", [])[:5],
                                lambda q: rx.text(
                                    f"第{q.get('id', '?')}题：{q.get('question', '')[:50]}",
                                    size="2",
                                    color="var(--gray-11)",
                                ),
                            ),
                            direction="column",
                            spacing="3",
                        ),
                        width="100%",
                        size="3",
                        variant="surface",
                        border_left="4px solid var(--green-6)",
                    ),
                ),
                rx.flex(
                    rx.button(
                        rx.icon("save", size=16),
                        "保存题库",
                        size="3",
                        color_scheme="green",
                        variant="solid",
                        on_click=AdminState.confirm_preview,
                        disabled=AdminState.preview_bank == {},
                    ),
                    rx.button(
                        rx.icon("x", size=16),
                        "取消",
                        size="3",
                        variant="outline",
                        on_click=AdminState.discard_preview,
                    ),
                    spacing="3",
                ),
                direction="column",
                spacing="4",
                width="100%",
                max_width="900px",
                align="center",
                padding_y="4",
            ),
            value="file",
        ),
        # Tab 3: Offline upload
        rx.tabs.content(
            rx.flex(
                rx.card(
                    rx.flex(
                        rx.flex(
                            rx.icon("folder-down", size=32, color="var(--blue-9)"),
                            rx.text("离线上传说明", size="4", weight="bold"),
                            spacing="3",
                        ),
                        rx.divider(),
                        rx.text(
                            "将处理好的题库文件（.json 或 .md）放入以下目录：",
                            size="3",
                        ),
                        rx.code_block(
                            "data/import/",
                            language="bash",
                            line_numbers=False,
                            wrap_long_lines=True,
                            theme="dark",
                        ),
                        rx.text(
                            "系统会自动检测并解析文件，处理完成后自动删除原始文件。",
                            size="3",
                            color="var(--gray-9)",
                        ),
                        direction="column",
                        spacing="3",
                    ),
                    width="100%",
                    size="3",
                    variant="surface",
                ),
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "刷新文件列表",
                    size="3",
                    variant="outline",
                    on_click=AdminState.refresh_import_files,
                ),
                rx.cond(
                    AdminState.import_files != [],
                    rx.foreach(
                        AdminState.import_files,
                        lambda f: rx.flex(
                            rx.flex(
                                rx.text(f["filename"], size="3", weight="medium"),
                                rx.text(
                                    f"{f.get('size', 0) / 1024:.1f} KB",
                                    size="2",
                                    color="var(--gray-8)",
                                ),
                                spacing="2",
                            ),
                            rx.flex(
                                rx.button(
                                    rx.icon("file-check", size=16),
                                    "处理",
                                    size="2",
                                    color_scheme="green",
                                    variant="soft",
                                    on_click=AdminState.process_import_file(f["filename"]),
                                ),
                                rx.button(
                                    rx.icon("trash-2", size=16),
                                    size="2",
                                    variant="soft",
                                    color_scheme="red",
                                    on_click=AdminState.clean_import_file(f["filename"]),
                                ),
                                spacing="2",
                            ),
                            width="100%",
                            justify="between",
                            align="center",
                            padding_y="2",
                            border_bottom="1px solid var(--gray-3)",
                        ),
                    ),
                ),
                rx.cond(
                    AdminState.upload_status != "",
                    rx.toast(
                        AdminState.upload_status,
                        position="bottom",
                        color_scheme=rx.cond(AdminState.upload_status.contains("成功"), "blue", "red"),
                    )
                ),
                direction="column",
                spacing="4",
                width="100%",
                max_width="900px",
            ),
            value="offline",
        ),
        # Tab 4: Bank management
        rx.tabs.content(
            rx.flex(
                rx.foreach(
                    AdminState.bank_list,
                    lambda bank: rx.flex(
                        rx.flex(
                            rx.text(bank.get("name", "未命名"), size="3", weight="medium"),
                            rx.text(
                                f"{bank.get('description', '')[:50] + (rx.cond(bank.get('description', '').length() > 50, '...', ''))}",
                                size="2",
                                color="var(--gray-8)",
                                style={"fontStyle": "italic"},
                            ),
                            spacing="2",
                        ),
                        rx.text(
                            f"{AdminState._format_time(bank.get('modified', 0))}",
                            size="2",
                            color="var(--gray-7)",
                        ),
                        spacing="2",
                    ),
                    rx.flex(
                        rx.button(
                            rx.icon("pencil", size=16),
                            size="2",
                            variant="soft",
                            color_scheme="blue",
                            on_click=AdminState.set_show_delete_confirm(f"rename:{bank['filename']}"),
                            tooltip="重命名",
                        ),
                        rx.button(
                            rx.icon("pencil-line", size=16),
                            size="2",
                            variant="soft",
                            color_scheme="yellow",
                            on_click=AdminState.set_show_delete_confirm(f"edit_desc:{bank['filename']}"),
                            tooltip="编辑描述",
                        ),
                        rx.button(
                            rx.icon("trash-2", size=16),
                            size="2",
                            variant="soft",
                            color_scheme="red",
                            on_click=AdminState.set_show_delete_confirm(f"delete:{bank['filename']}"),
                            tooltip="删除",
                        ),
                        spacing="2",
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    padding_y="2",
                    border_bottom="1px solid var(--gray-3)"
                ),
                rx.cond(
                    AdminState.upload_status != "",
                    rx.toast(
                        AdminState.upload_status,
                        position="bottom",
                        color_scheme=rx.cond(AdminState.upload_status.contains("成功"), "blue", "red"),
                    ),
                ),
                rx.cond(
                    AdminState.show_delete_confirm.startswith("rename:"),
                    rx.modal.root(
                        rx.modal.content(
                            rx.modal.header("重命名题库"),
                            rx.modal.body(
                                rx.input(
                                    placeholder="新名称",
                                    value=AdminState.rename_new_name,
                                    on_change=AdminState.set_rename_new_name,
                                ),
                            ),
                            rx.modal.footer(
                                rx.button(
                                    "取消",
                                    variant="soft",
                                    color_scheme="gray",
                                    on_click=AdminState.set_show_delete_confirm(""),
                                ),
                                rx.button(
                                    "确认",
                                    color_scheme="blue",
                                    on_click=[
                                        AdminState.rename_bank(
                                            AdminState.show_delete_confirm.replace("rename:", ""),
                                            AdminState.rename_new_name,
                                        ),
                                        AdminState.set_show_delete_confirm(""),
                                        AdminState.set_rename_new_name(""),
                                    ],
                                ),
                            ),
                        ),
                        open=AdminState.show_delete_confirm.startswith("rename:"),
                    ),
                ),
                rx.cond(
                    AdminState.show_delete_confirm.startswith("edit_desc:"),
                    rx.modal.root(
                        rx.modal.content(
                            rx.modal.header("编辑题库描述"),
                            rx.modal.body(
                                rx.text_area(
                                    placeholder="请输入或修改题库描述...",
                                    value=AdminState.bank_description,
                                    on_change=AdminState.set_bank_description,
                                    height="100px",
                                ),
                            ),
                            rx.modal.footer(
                                rx.button(
                                    "取消",
                                    variant="soft",
                                    color_scheme="gray",
                                    on_click=AdminState.set_show_delete_confirm(""),
                                ),
                                rx.button(
                                    "保存",
                                    color_scheme="green",
                                    on_click=[
                                        AdminState.save_bank_description(
                                            AdminState.show_delete_confirm.replace("edit_desc:", ""),
                                            AdminState.bank_description,
                                        ),
                                        AdminState.set_show_delete_confirm(""),
                                    ],
                                ),
                            ),
                        ),
                        open=AdminState.show_delete_confirm.startswith("edit_desc:"),
                    ),
                ),
                rx.cond(
                    AdminState.show_delete_confirm.startswith("delete:"),
                    rx.modal.root(
                        rx.modal.content(
                            rx.modal.header("确认删除"),
                            rx.modal.body(
                                rx.text("确定要删除此题库吗？此操作不可撤销。"),
                            ),
                            rx.modal.footer(
                                rx.button(
                                    "取消",
                                    variant="soft",
                                    color_scheme="gray",
                                    on_click=AdminState.set_show_delete_confirm(""),
                                ),
                                rx.button(
                                    "删除",
                                    color_scheme="red",
                                    on_click=[
                                        AdminState.delete_bank(
                                            AdminState.show_delete_confirm.replace("delete:", ""),
                                        ),
                                        AdminState.set_show_delete_confirm(""),
                                    ],
                                ),
                            ),
                        ),
                        open=AdminState.show_delete_confirm.startswith("delete:"),
                    ),
                ),
                direction="column",
                spacing="4",
                width="100%",
                max_width="900px",
                value="manage",
            ),
            width="100%",
            max_width="900px",
            padding_x="4",
            padding_y="8",
            default_value="text",
            color_scheme="gray",
            variant="solid",
            on_change=AdminState.set_upload_tab,
        )
    )