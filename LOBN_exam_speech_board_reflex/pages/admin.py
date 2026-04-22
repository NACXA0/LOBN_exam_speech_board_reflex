# 后台管理页面

import reflex as rx
from LOBN_exam_speech_board_reflex.state import AdminState


# ============================================================
# 以下是 admin 页面的组件，拆分为独立变量以隔离括号嵌套
# ============================================================

def _upload_status_text() -> rx.Component:
    """上传状态文本 - 长期状态显示."""
    return rx.cond(
        AdminState.upload_status != "",
        rx.text(
            AdminState.upload_status,
            size="2",
            color=rx.cond(AdminState.upload_status.contains("成功"), "var(--blue-9)", "var(--red-9)"),
            weight="medium",
        ),
    )


def _preview_brief_card() -> rx.Component:
    """简要预览卡片 - Tab2 复用."""
    return rx.cond(
        AdminState.has_preview,
        rx.card(
            rx.flex(
                rx.text("预览", size="4", weight="bold"),
                rx.divider(),
                rx.foreach(
                    AdminState.preview_questions_brief,
                    lambda q: rx.text(
                        q["display_brief"],
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
    )


def _save_cancel_buttons() -> rx.Component:
    """保存/取消按钮组 - 多个 Tab 复用."""
    return rx.flex(
        rx.button(
            rx.icon("save", size=16),
            "保存题库",
            size="3",
            color_scheme="green",
            variant="solid",
            on_click=AdminState.confirm_preview,
            disabled=~AdminState.has_preview,
        ),
        rx.button(
            rx.icon("x", size=16),
            "取消",
            size="3",
            variant="outline",
            on_click=AdminState.discard_preview,
        ),
        spacing="3",
    )


# ---- Tab 1: 在线上传 ----

def _tab1_preview_mode() -> rx.Component:
    """Tab1 预览模式."""
    return rx.flex(
        rx.card(
            rx.flex(
                rx.text("预览", size="4", weight="bold"),
                rx.text(
                    f"{AdminState.preview_total_questions} 道题",
                    size="3",
                    color="var(--gray-9)",
                ),
                spacing="3",
            ),
            rx.divider(),
            rx.foreach(
                AdminState.preview_questions_formatted,
                lambda questions: rx.flex(
                    rx.badge(
                        rx.text(questions["display_id"], size="2"),
                        size="1",
                        color_scheme="gray",
                        variant="outline",
                    ),
                    rx.text(
                        questions["display_question"],
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
            AdminState.preview_total_questions > 5,
            rx.text(
                f"... 共 {AdminState.preview_total_questions} 道题",
                size="2",
                color="var(--gray-8)",
                style={"fontStyle": "italic"},
            ),
        ),
        direction="column",
        spacing="3",
    )


def _tab1_edit_mode() -> rx.Component:
    """Tab1 编辑模式."""
    return rx.flex(
        rx.input(
            placeholder="输入题库名称",
            value=AdminState.new_bank_name,
            on_change=AdminState.set_new_bank_name,
            width="100%",
            size="3",
            variant="classic",
        ),
        rx.input(
            placeholder="题库描述（可选）",
            value=AdminState.bank_description,
            on_change=AdminState.set_bank_description,
            width="100%",
            size="3",
            variant="classic",
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
        ),
        rx.flex(
            rx.button(
                rx.icon("eye", size=16),
                "预览",
                size="3",
                variant="outline",
                on_click=AdminState.handle_text_upload(
                    AdminState.text_content,
                    rx.cond(AdminState.new_bank_name != '', AdminState.new_bank_name, "untitled.txt"),
                ),
            ),
            rx.button(
                rx.icon("save", size=16),
                "保存",
                size="3",
                color_scheme="green",
                variant="solid",
                on_click=AdminState.confirm_preview,
                disabled=~AdminState.has_preview,
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
        _upload_status_text(),
        direction="column",
        spacing="4",
        width="100%",
        max_width="900px",
    )


def _tab1_content() -> rx.Component:
    """Tab 1: 在线上传."""
    return rx.tabs.content(
        rx.cond(AdminState.has_preview, _tab1_preview_mode()),
        rx.cond(~AdminState.has_preview, _tab1_edit_mode()),
        value="text",
    )


# ---- Tab 2: 文件上传 ----

def _tab2_content() -> rx.Component:
    """Tab 2: 文件上传."""
    return rx.tabs.content(
        rx.flex(
            rx.cond(
                AdminState.uploaded_file != None,
                rx.card(
                    rx.flex(
                        rx.icon("file-check", size=48, color="var(--green-9)"),
                        rx.text(
                            AdminState.uploaded_file.filename,
                            size="3",
                            weight="medium",
                        ),
                        rx.text(
                            AdminState.uploaded_file_size_kb,
                            size="2",
                            color="var(--gray-8)",
                        ),
                        spacing="2",
                    ),
                    width="100%",
                    size="3",
                    variant="surface",
                ),
            ),
            rx.cond(
                AdminState.uploaded_file == None,
                rx.upload(
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
                    id="admin_file_upload",
                    multiple=False,
                    accept={
                        "text/plain": [".txt"],
                        "text/markdown": [".md"],
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                    },
                    on_drop=AdminState.handle_file_upload,
                ),
            ),
            _upload_status_text(),
            _preview_brief_card(),
            _save_cancel_buttons(),
            direction="column",
            spacing="4",
            width="100%",
            max_width="900px",
            align="center",
            padding_y="4",
        ),
        value="file",
    )


# ---- Tab 3: 离线上传 ----

def _tab3_content() -> rx.Component:
    """Tab 3: 离线上传."""
    return rx.tabs.content(
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
                AdminState.import_files_with_size.length() > 0,
                rx.foreach(
                    AdminState.import_files_with_size,
                    lambda f: rx.flex(
                        rx.flex(
                            rx.text(f["filename"], size="3", weight="medium"),
                            rx.text(
                                f.get("size_kb", "0 KB"),
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
            _upload_status_text(),
            direction="column",
            spacing="4",
            width="100%",
            max_width="900px",
        ),
        value="offline",
    )


# ---- Tab 4: 题库管理 ----

def _rename_modal() -> rx.Component:
    """重命名弹窗."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("重命名题库"),
            rx.input(
                placeholder="新名称",
                value=AdminState.rename_new_name,
                on_change=AdminState.set_rename_new_name,
            ),
            rx.dialog.close(
                rx.flex(
                    rx.button(
                        "取消",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.close_action_dialog,
                    ),
                    rx.button(
                        "确认",
                        color_scheme="blue",
                        on_click=[
                            AdminState.rename_bank(
                                AdminState.current_action_bank_filename,
                                AdminState.rename_new_name,
                            ),
                            AdminState.close_action_dialog,
                            AdminState.set_rename_new_name(""),
                        ],
                    ),
                    spacing="2",
                )
            ),
        ),
        open=AdminState.current_action_type == "rename",
    )


def _edit_desc_modal() -> rx.Component:
    """编辑描述弹窗."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("编辑题库描述"),
            rx.text_area(
                placeholder="请输入或修改题库描述...",
                value=AdminState.bank_description,
                on_change=AdminState.set_bank_description,
                height="100px",
            ),
            rx.dialog.close(
                rx.flex(
                    rx.button(
                        "取消",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.close_action_dialog,
                    ),
                    rx.button(
                        "保存",
                        color_scheme="green",
                        on_click=[
                            AdminState.save_bank_description(
                                AdminState.current_action_bank_filename,
                                AdminState.bank_description,
                            ),
                            AdminState.close_action_dialog,
                        ],
                    ),
                    spacing="2",
                )
            ),
        ),
        open=AdminState.current_action_type == "edit_desc",
    )


def _delete_modal() -> rx.Component:
    """删除确认弹窗."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("确认删除"),
            rx.dialog.description(
                "确定要删除此题库吗？此操作不可撤销。"
            ),
            rx.dialog.close(
                rx.flex(
                    rx.button(
                        "取消",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.close_action_dialog,
                    ),
                    rx.button(
                        "删除",
                        color_scheme="red",
                        on_click=[
                            AdminState.delete_bank(
                                AdminState.current_action_bank_filename,
                            ),
                            AdminState.close_action_dialog,
                        ],
                    ),
                    spacing="2",
                )
            ),
        ),
        open=AdminState.current_action_type == "delete",
    )


def _tab4_content() -> rx.Component:
    """Tab 4: 题库管理."""
    return rx.tabs.content(
        rx.flex(
            rx.foreach(
                AdminState.bank_list_formatted,
                lambda bank: rx.flex(
                    rx.flex(
                        rx.text(
                            bank.get("name", "未命名"),
                            size="3",
                            weight="medium",
                        ),
                        rx.text(
                            bank["display_description"],
                            size="2",
                            color="var(--gray-8)",
                            style={"fontStyle": "italic"},
                        ),
                        spacing="2",
                    ),
                    rx.text(
                        bank["display_modified"],
                        size="2",
                        color="var(--gray-7)",
                    ),
                    rx.flex(
                        rx.button(
                            rx.icon("pencil", size=16),
                            size="2",
                            variant="soft",
                            color_scheme="blue",
                            on_click=AdminState.open_action_dialog("rename", bank["filename"]),
                            tooltip="重命名",
                        ),
                        rx.button(
                            rx.icon("pencil-line", size=16),
                            size="2",
                            variant="soft",
                            color_scheme="yellow",
                            on_click=AdminState.open_action_dialog("edit_desc", bank["filename"]),
                            tooltip="编辑描述",
                        ),
                        rx.button(
                            rx.icon("trash-2", size=16),
                            size="2",
                            variant="soft",
                            color_scheme="red",
                            on_click=AdminState.open_action_dialog("delete", bank["filename"]),
                            tooltip="删除",
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
            _upload_status_text(),
            _rename_modal(),
            _edit_desc_modal(),
            _delete_modal(),
            direction="column",
            spacing="4",
            width="100%",
            max_width="900px",
        ),
        value="manage",
    )


# ============================================================
# 页面入口：组装所有 Tab
# ============================================================

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
            _tab1_content(),
            _tab2_content(),
            _tab3_content(),
            _tab4_content(),
            default_value="text",
            color_scheme="gray",
            variant="solid",
            on_change=AdminState.set_upload_tab,
            width="100%",
            max_width="900px",
            padding_x="4",
            padding_y="8",
        ),
    )
