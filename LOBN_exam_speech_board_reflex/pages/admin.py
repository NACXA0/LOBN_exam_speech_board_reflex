# 后台管理页面

import reflex as rx
from LOBN_exam_speech_board_reflex.state import AdminState, AppState


# ============================================================
# 以下是 admin 页面的组件，拆分为独立变量以隔离括号嵌套
# ============================================================

def _upload_status_text() -> rx.Component:
    """上传状态文本 - 仅在Tab1在线上传中使用."""
    return rx.cond(
        AdminState.upload_status != "",
        rx.flex(
            rx.icon(
                rx.cond(AdminState.upload_status.contains("成功"), "check-circle", "alert-circle"),
                size=14,
                color=rx.cond(AdminState.upload_status.contains("成功"), "var(--green-9)", "var(--red-9)"),
            ),
            rx.text(
                AdminState.upload_status,
                size="2",
                color=rx.cond(AdminState.upload_status.contains("成功"), "var(--green-9)", "var(--red-9)"),
                weight="medium",
            ),
            spacing="1",
            align="center",
        ),
    )


def _action_status_text() -> rx.Component:
    """操作反馈状态文本 - 仅在Tab2题库管理中使用."""
    return rx.cond(
        AdminState.action_status != "",
        rx.flex(
            rx.icon(
                rx.cond(AdminState.action_status.contains("失败"), "alert-circle", "check-circle"),
                size=14,
                color=rx.cond(AdminState.action_status.contains("失败"), "var(--red-9)", "var(--green-9)"),
            ),
            rx.text(
                AdminState.action_status,
                size="2",
                color=rx.cond(AdminState.action_status.contains("失败"), "var(--red-9)", "var(--green-9)"),
                weight="medium",
            ),
            spacing="1",
            align="center",
        ),
    )




# Tab： 选择题目进入演讲白板

def _bank_card(bank: dict) -> rx.Component:
    """Render a single question bank card."""
    total_q = bank.get("total_questions", 0)
    modified = bank.get("modified_str", "未知")
    return rx.card(
        rx.flex(
            # 顶部：图标 + 题库名
            rx.flex(
                rx.icon("book-open", size=22, color="var(--gray-11)"),
                rx.text(
                    bank.get("name", "未命名题库"),
                    size="4",
                    weight="bold",
                    color="var(--gray-12)",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            # 中部：题目数量 + 修改时间
            rx.flex(
                rx.badge(
                    rx.flex(
                        rx.icon("list-ordered", size=12),
                        rx.text(f"{total_q} 题", size="1"),
                        spacing="1",
                        align="center",
                    ),
                    color_scheme="blue",
                    variant="soft",
                ),
                rx.text(
                    modified,
                    size="1",
                    color="var(--gray-8)",
                ),
                spacing="2",
                align="center",
            ),
            # 底部：开始按钮
            rx.button(
                "开始讲题",
                rx.icon("chevron-right", size=16),
                size="2",
                color_scheme="green",
                variant="solid",
                width="100%",
                on_click=[
                    AppState.load_bank(bank["filename"]),
                    rx.redirect("/workspace")
                ],
            ),
            direction="column",
            spacing="2",
            width="100%",
        ),
        width="calc(50% - 0.375rem)",
        size="2",
        variant="surface",
        _hover={"shadow": "md"},
    )


def _tab1_wellcome() -> rx.Component:
    """选择题库页面."""
    return rx.tabs.content(
        rx.flex(
            rx.heading("鲁班讲题白板", size="8", weight="bold", color="var(--gray-12)"),
            rx.text(
                "请选择一个题库开始讲题",
                size="4",
                color="var(--gray-9)",
            ),
            direction="column",
            align_items="center",
            width="100%",
            style={"padding_top": "6rem", "padding_bottom": "4rem"},
        ),
        rx.flex(
            rx.foreach(
                AppState.bank_list,
                _bank_card,
            ),
            direction="row",
            wrap="wrap",
            spacing="3",
            width="100%",
        ),
        rx.cond(
            AppState.bank_list == [],
            rx.flex(
                rx.text("暂无题库，请到后台上传题库文件"),
                justify_content="center",
                width="100%",
                style={"padding_top": "8rem", "padding_bottom": "8rem"},
            ),
        ),
        max_width="60rem",
        width="100%",
        value="wellcome",
        style={"padding_left": "4rem", "padding_right": "4rem", "padding_bottom": "8rem"},
    )


# ---- Tab 1: 在线上传 ----

def _question_preview_item(question) -> rx.Component:
    """Render single question preview item."""
    return rx.card(
        rx.flex(
            # === 顶部：题号 + 答案 ===
            rx.flex(
                rx.badge(
                    question["display_id"],
                    size="1",
                    color_scheme="blue",
                    variant="solid",
                    weight="bold",
                ),
                rx.cond(
                    question["has_answer"].to(bool),
                    rx.badge(
                        rx.text("答案：", size="1", weight="bold"),
                        rx.text(question["display_answer"], size="1"),
                        size="1",
                        color_scheme="green",
                        variant="soft",
                    ),
                ),
                rx.spacer(),
                rx.cond(
                    question["has_explanation"].to(bool),
                    rx.badge(
                        rx.icon("lightbulb", size=12),
                        rx.text("有解析", size="1"),
                        size="1",
                        color_scheme="amber",
                        variant="soft",
                    ),
                ),
                width="100%",
                align="center",
            ),
            # === 题干 ===
            rx.text(
                question["display_question"],
                size="3",
                weight="bold",
                color="var(--gray-12)",
                line_height="1.7",
                padding_top="2",
                padding_bottom="2",
            ),
            # === 选项列表 ===
            rx.cond(
                question["has_options"].to(bool),
                rx.grid(
                    rx.foreach(
                        question["display_options_list"].to(list),
                        lambda opt: rx.flex(
                            rx.badge(
                                opt.to(dict)["letter"],
                                size="1",
                                color_scheme="gray",
                                variant="outline",
                                width="1.75rem",
                                height="1.75rem",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                                weight="bold",
                            ),
                            rx.text(
                                opt.to(dict)["text"],
                                size="2",
                                color="var(--gray-11)",
                                flex="1",
                                line_height="1.6",
                            ),
                            spacing="2",
                            align="center",
                            padding="0.5rem 0.75rem",
                            background="var(--gray-2)",
                            border_radius="0.375rem",
                            border="0.0625rem solid var(--gray-3)",
                        ),
                    ),
                    columns="2",
                    spacing="2",
                    width="100%",
                    padding_top="1",
                    padding_bottom="2",
                ),
            ),
            # === 解析 ===
            rx.cond(
                question["has_explanation"].to(bool),
                rx.flex(
                    rx.box(
                        rx.flex(
                            rx.icon("lightbulb", size=14, color="var(--amber-9)"),
                            rx.text("解析", size="2", weight="bold", color="var(--amber-10)"),
                            spacing="1",
                            align="center",
                        ),
                        padding_bottom="1",
                    ),
                    rx.text(
                        question["display_explanation"],
                        size="2",
                        color="var(--gray-10)",
                        line_height="1.7",
                    ),
                    direction="column",
                    spacing="1",
                    padding="0.75rem",
                    background="var(--amber-2)",
                    border_radius="0.375rem",
                    border_left="0.1875rem solid var(--amber-6)",
                    width="100%",
                ),
            ),
            direction="column",
            spacing="2",
        ),
        width="100%",
        size="2",
        variant="surface",
        padding="4",
    )


def _preview_option_item(opt) -> rx.Component:
    """Render single option preview item."""
    return rx.flex(
        rx.badge(
            opt.to(dict)["letter"],
            size="1",
            color_scheme="gray",
            variant="soft",
            width="1.5rem",
            height="1.5rem",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        rx.text(
            opt.to(dict)["text"],
            size="2",
            color="var(--gray-11)",
            flex="1",
        ),
        spacing="2",
        align="center",
        padding="0.375rem 0",
    )


def _tab2_upload() -> rx.Component:
    """Tab 1: 在线上传 - 左右分栏实时预览."""
    # 顶部操作按钮栏
    def top_bar() -> rx.Component:
        return rx.flex(
            rx.button(
                rx.icon("save", size=16),
                "保存题库",
                size="2",
                color_scheme="green",
                variant="solid",
                on_click=AdminState.confirm_preview,
                disabled=~AdminState.has_preview,
            ),
            rx.button(
                rx.icon("download", size=16),
                "下载示例",
                size="2",
                variant="outline",
                on_click=AdminState.download_sample_json,
                tooltip="下载符合本系统格式的示例JSON文件",
            ),
            rx.upload.root(
                rx.button(
                    rx.icon("file-up", size=16),
                    "上传题库文件",
                    size="2",
                    variant="outline",
                    #on_click=rx.upload_files(upload_id="inline_file_upload"),
                ),
                id="inline_file_upload",
                multiple=False,
                no_drag=True,
                no_keyboard=True,
                no_list=True,
                accept={
                    "text/plain": [".txt"],
                    "text/markdown": [".md"],
                    "application/msword": [".doc"],
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                    "application/json": [".json"],
                },
                on_drop=AdminState.handle_inline_file_upload,
            ),
            _upload_status_text(),
            rx.spacer(),
            # 三段式布局切换按钮
            rx.flex(
                rx.button(
                    rx.icon("panel-left-open", size=16),
                    "输入",
                    size="2",
                    variant=rx.cond(
                        ~AdminState.show_preview & AdminState.show_input_panel,
                        "solid",
                        "outline"
                    ),
                    color_scheme=rx.cond(
                        ~AdminState.show_preview & AdminState.show_input_panel,
                        "blue",
                        "gray"
                    ),
                    on_click=[
                        AdminState.set_show_input_panel(True),
                        AdminState.set_show_preview(False),
                    ],
                    tooltip="仅显示输入框",
                ),
                rx.button(
                    rx.icon("columns", size=16),
                    "双栏",
                    size="2",
                    variant=rx.cond(
                        AdminState.show_preview & AdminState.show_input_panel,
                        "solid",
                        "outline"
                    ),
                    color_scheme=rx.cond(
                        AdminState.show_preview & AdminState.show_input_panel,
                        "blue",
                        "gray"
                    ),
                    on_click=[
                        AdminState.set_show_input_panel(True),
                        AdminState.set_show_preview(True),
                    ],
                    tooltip="输入框和预览框各占一半",
                ),
                rx.button(
                    rx.icon("panel-right-open", size=16),
                    "预览",
                    size="2",
                    variant=rx.cond(
                        AdminState.show_preview & ~AdminState.show_input_panel,
                        "solid",
                        "outline"
                    ),
                    color_scheme=rx.cond(
                        AdminState.show_preview & ~AdminState.show_input_panel,
                        "blue",
                        "gray"
                    ),
                    on_click=[
                        AdminState.set_show_input_panel(False),
                        AdminState.set_show_preview(True),
                    ],
                    tooltip="仅显示预览框",
                ),
                spacing="2",
            ),
            spacing="3",
            align="center",
            width="100%",
        )

    # 左侧：输入区域
    def input_area() -> rx.Component:
        return rx.flex(
            # 输入框区域
            rx.flex(
                rx.input(
                    placeholder="输入题库名称",
                    value=AdminState.new_bank_name,
                    on_change=AdminState.set_new_bank_name,
                    width="100%",
                    size="2",
                    variant="classic",
                ),
                rx.input(
                    placeholder="题库描述（可选）",
                    value=AdminState.bank_description,
                    on_change=AdminState.set_bank_description,
                    width="100%",
                    size="2",
                    variant="classic",
                ),
                rx.text_area(
                    placeholder=(
                        "在此输入题库内容，右侧自动预览...\n\n"
                        "支持格式：\n"
                        "1、题目编号  A.选项  B.选项\n"
                        "答案：D\n"
                        "解析：..."
                    ),
                    value=AdminState.text_content,
                    on_change=AdminState.set_text_content,
                    width="100%",
                    height="28.75rem",
                    size="2",
                    variant="classic",
                    font_family="monospace",
                ),
                direction="column",
                spacing="3",
                flex="1",
            ),
            direction="column",
            spacing="3",
            flex="1",
            min_width="0",
        )

    # 右侧：实时预览面板
    def view_area() -> rx.Component:
        return rx.box(
            rx.flex(
                # 预览标题栏
                rx.flex(
                    rx.flex(
                        rx.icon("eye", size=14, color="var(--gray-9)"),
                        rx.text("实时预览", size="3", weight="bold"),
                        rx.cond(
                            AdminState.has_preview,
                            rx.badge(
                                f"{AdminState.preview_total_questions} 题",
                                size="1",
                                color_scheme="green",
                                variant="soft",
                            ),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                    padding_bottom="3",
                    border_bottom="0.0625rem solid var(--gray-4)",
                ),
                # 可折叠的预览内容
                rx.cond(
                    AdminState.has_preview,
                    # 有预览：显示题目列表
                    rx.flex(
                        rx.foreach(
                            AdminState.preview_questions_formatted,
                            lambda question: _question_preview_item(question),
                        ),
                        spacing="3",
                        direction="column",
                        overflow_y="auto",
                        padding_top="2",
                        width="100%",
                    ),
                    # 无预览：占位提示
                    rx.flex(
                        rx.icon("file-text", size=32, color="var(--gray-6)"),
                        rx.text("输入题目内容后自动预览", size="2", color="var(--gray-8)"),
                        rx.text("支持 1、题号 + A.选项 格式", size="1", color="var(--gray-7)"),
                        direction="column",
                        align="center",
                        spacing="2",
                        padding_y="8",
                    ),
                ),
                direction="column",
                spacing="3",
                height="100%",
            ),
            flex="1",
            padding="4",
            background="var(--gray-2)",
            border_radius="0.5rem",
            border="0.0625rem solid var(--gray-3)",
        )

    return rx.tabs.content(
        # 顶部操作按钮栏
        top_bar(),
        rx.flex(
            # ===== 左侧：输入区域 =====
            rx.cond(
                AdminState.show_input_panel,
                input_area()
            ),
            # ===== 右侧：实时预览面板 =====
            rx.cond(
                AdminState.show_preview,
                view_area()
            ),
            direction="row",
            spacing="4",
            width="100%",
            align="stretch",
        ),
        width="100%",
        value="text",
    )


# ---- Tab 2: 题库管理 ----

def _rename_modal() -> rx.Component:
    """重命名弹窗."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("重命名题库"),
            rx.dialog.description("输入新的题库名称"),
            rx.input(
                placeholder="新名称",
                value=AdminState.rename_new_name,
                on_change=AdminState.set_rename_new_name,
                size="2",
            ),
            rx.flex(
                rx.button(
                    "取消",
                    variant="soft",
                    color_scheme="gray",
                    on_click=AdminState.close_action_dialog,
                ),
                rx.button(
                    "确认重命名",
                    color_scheme="blue",
                    on_click=[
                        AdminState.rename_bank(
                            AdminState.current_action_bank_filename,
                            AdminState.rename_new_name,
                        ),
                        AdminState.close_action_dialog,
                    ],
                ),
                spacing="3",
                justify="end",
                padding_top="4",
            ),
        ),
        open=AdminState.current_action_type == "rename",
        on_open_change=AdminState.close_action_dialog,
    )


def _edit_desc_modal() -> rx.Component:
    """编辑描述弹窗."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("编辑题库描述"),
            rx.dialog.description("修改题库的描述信息"),
            rx.text_area(
                placeholder="请输入或修改题库描述...",
                value=AdminState.bank_description,
                on_change=AdminState.set_bank_description,
                height="6.25rem",
                size="2",
            ),
            rx.flex(
                rx.button(
                    "取消",
                    variant="soft",
                    color_scheme="gray",
                    on_click=AdminState.close_action_dialog,
                ),
                rx.button(
                    "保存描述",
                    color_scheme="green",
                    on_click=[
                        AdminState.save_bank_description(
                            AdminState.current_action_bank_filename,
                            AdminState.bank_description,
                        ),
                        AdminState.close_action_dialog,
                    ],
                ),
                spacing="3",
                justify="end",
                padding_top="4",
            ),
        ),
        open=AdminState.current_action_type == "edit_desc",
        on_open_change=AdminState.close_action_dialog,
    )


def _delete_modal() -> rx.Component:
    """删除确认弹窗."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("确认删除"),
            rx.dialog.description(
                "确定要删除此题库吗？此操作不可撤销。"
            ),
            rx.flex(
                rx.button(
                    "取消",
                    variant="soft",
                    color_scheme="gray",
                    on_click=AdminState.close_action_dialog,
                ),
                rx.button(
                    "确认删除",
                    color_scheme="red",
                    on_click=[
                        AdminState.delete_bank(
                            AdminState.current_action_bank_filename,
                        ),
                        AdminState.close_action_dialog,
                    ],
                ),
                spacing="3",
                justify="end",
                padding_top="4",
            ),
        ),
        open=AdminState.current_action_type == "delete",
        on_open_change=AdminState.close_action_dialog,
    )


def _tab3_manage() -> rx.Component:
    """Tab 2: 题库管理."""
    return rx.tabs.content(
        rx.flex(
            # ---- 排序控制栏 ----
            rx.flex(
                rx.text("排序：", size="2", weight="medium", color="var(--gray-9)"),
                rx.button(
                    rx.icon("clock", size=14),
                    "编辑时间",
                    size="2",
                    variant=rx.cond(AdminState.bank_sort_field == "modified", "solid", "outline"),
                    color_scheme=rx.cond(AdminState.bank_sort_field == "modified", "blue", "gray"),
                    on_click=AdminState.set_bank_sort("modified"),
                ),
                rx.button(
                    rx.icon("hash", size=14),
                    "题目数",
                    size="2",
                    variant=rx.cond(AdminState.bank_sort_field == "total_questions", "solid", "outline"),
                    color_scheme=rx.cond(AdminState.bank_sort_field == "total_questions", "blue", "gray"),
                    on_click=AdminState.set_bank_sort("total_questions"),
                ),
                rx.button(
                    rx.icon("text", size=14),
                    "名称",
                    size="2",
                    variant=rx.cond(AdminState.bank_sort_field == "name", "solid", "outline"),
                    color_scheme=rx.cond(AdminState.bank_sort_field == "name", "blue", "gray"),
                    on_click=AdminState.set_bank_sort("name"),
                ),
                rx.text(
                    AdminState.bank_sort_indicator,
                    size="3",
                    weight="bold",
                    color="var(--blue-9)",
                ),
                rx.spacer(),
                _action_status_text(),
                spacing="2",
                align="center",
                width="100%",
                padding_y="3",
            ),
            # ---- 题库列表 ----
            rx.foreach(
                AdminState.bank_list_formatted,
                lambda bank: rx.card(
                    rx.flex(
                        # 左侧：题库信息
                        rx.flex(
                            # 第一行：名称 + badges
                            rx.flex(
                                rx.text(
                                    bank.get("name", "未命名"),
                                    size="4",
                                    weight="bold",
                                ),
                                rx.badge(
                                    f"{bank['display_total_questions']} 题",
                                    size="1",
                                    color_scheme="blue",
                                    variant="soft",
                                ),
                                rx.badge(
                                    bank["display_size"],
                                    size="1",
                                    color_scheme="gray",
                                    variant="outline",
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                            ),
                            # 第二行：描述
                            rx.text(
                                bank["display_description"],
                                size="2",
                                color="var(--gray-8)",
                                style={"fontStyle": "italic"},
                            ),
                            # 第三行：修改时间
                            rx.flex(
                                rx.icon("clock", size=12, color="var(--gray-7)"),
                                rx.text(
                                    bank["display_modified"],
                                    size="1",
                                    color="var(--gray-7)",
                                ),
                                spacing="1",
                                align="center",
                            ),
                            direction="column",
                            spacing="2",
                            flex="1",
                            min_width="0",
                        ),
                        # 右侧：操作按钮（带文字）
                        rx.flex(
                            rx.button(
                                rx.icon("list-checks", size=15),
                                "编辑试题",
                                size="2",
                                variant="solid",
                                color_scheme="green",
                                on_click=AdminState.open_edit_questions_new_tab(bank["filename"]),
                            ),
                            rx.button(
                                rx.icon("download", size=15),
                                "下载",
                                size="2",
                                variant="soft",
                                color_scheme="violet",
                                on_click=AdminState.download_bank_json(bank["filename"]),
                            ),
                            rx.button(
                                rx.icon("pencil", size=15),
                                "重命名",
                                size="2",
                                variant="soft",
                                color_scheme="blue",
                                on_click=AdminState.open_action_dialog("rename", bank["filename"]),
                            ),
                            rx.button(
                                rx.icon("file-pen", size=15),
                                "描述",
                                size="2",
                                variant="soft",
                                color_scheme="amber",
                                on_click=AdminState.open_action_dialog("edit_desc", bank["filename"]),
                            ),
                            rx.button(
                                rx.icon("trash-2", size=15),
                                "删除",
                                size="2",
                                variant="soft",
                                color_scheme="red",
                                on_click=AdminState.open_action_dialog("delete", bank["filename"]),
                            ),
                            spacing="2",
                            direction="column",
                        ),
                        width="100%",
                        justify="between",
                        align="start",
                    ),
                    width="100%",
                    size="2",
                    variant="surface",
                ),
            ),
            _rename_modal(),
            _edit_desc_modal(),
            _delete_modal(),
            direction="column",
            spacing="3",
            width="100%",
            max_width="56.25rem",
        ),
        value="manage",
    )


# ============================================================
# 页面入口：组装所有 Tab
# ============================================================

# ---- Tab 4: 白板设置 ----

def _tab4_settings() -> rx.Component:
    """Tab 4: 白板背景与水印设置."""
    return rx.tabs.content(
        rx.flex(
            rx.heading("白板外观设置", size="6", weight="bold", color="var(--gray-12)"),
            rx.divider(),
            # 背景颜色
            rx.flex(
                rx.text("背景颜色", size="3", weight="medium", color="var(--gray-11)", min_width="6rem"),
                rx.input(
                    type="color",
                    value=AdminState.whiteboard_bg_color,
                    on_change=AdminState.set_whiteboard_bg_color,
                    width="3rem",
                    height="2.5rem",
                    padding="0",
                    border="none",
                    style={"cursor": "pointer"},
                ),
                rx.input(
                    value=AdminState.whiteboard_bg_color,
                    on_change=AdminState.set_whiteboard_bg_color,
                    width="8rem",
                    size="2",
                    variant="classic",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            # 水印文字
            rx.flex(
                rx.text("水印文字", size="3", weight="medium", color="var(--gray-11)", min_width="6rem"),
                rx.input(
                    placeholder="输入水印文字或留空",
                    value=AdminState.whiteboard_watermark,
                    on_change=AdminState.set_whiteboard_watermark,
                    width="100%",
                    size="2",
                    variant="classic",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            # 水印文字透明度
            rx.cond(
                AdminState.whiteboard_watermark != "",
                rx.flex(
                    rx.text("水印文字透明度", size="3", weight="medium", color="var(--gray-11)", min_width="6rem"),
                    rx.slider(
                        default_value=[AdminState.whiteboard_watermark_text_opacity],
                        on_value_commit=AdminState.set_whiteboard_watermark_text_opacity,
                        min=0,
                        max=100,
                        step=5,
                        width="100%",
                    ),
                    rx.text(
                        f"{AdminState.whiteboard_watermark_text_opacity}%",
                        size="3",
                        color="var(--gray-11)",
                        min_width="3rem",
                        text_align="right",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
            ),
            # 水印图片
            rx.flex(
                rx.text("水印图片", size="3", weight="medium", color="var(--gray-11)", min_width="6rem"),
                rx.cond(
                    AdminState.whiteboard_watermark_image != "",
                    rx.flex(
                        rx.image(
                            src=rx.cond(
                                AdminState.whiteboard_watermark_image.startswith("data:") | AdminState.whiteboard_watermark_image.startswith("http://") | AdminState.whiteboard_watermark_image.startswith("https://"),
                                AdminState.whiteboard_watermark_image,
                                f"/assets/{AdminState.whiteboard_watermark_image}",
                            ),
                            width="3rem",
                            height="3rem",
                            object_fit="contain",
                        ),
                        rx.button(
                            rx.icon("trash-2", size=14),
                            "清除",
                            size="1",
                            variant="soft",
                            color_scheme="red",
                            on_click=AdminState.set_whiteboard_watermark_image(""),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.upload.root(
                        rx.button(
                            rx.icon("image-up", size=16),
                            "上传水印图片",
                            size="2",
                            variant="outline",
                        ),
                        id="watermark_image_upload",
                        multiple=False,
                        accept={
                            "image/png": [".png"],
                            "image/jpeg": [".jpg", ".jpeg"],
                            "image/webp": [".webp"],
                        },
                        on_drop=AdminState.handle_watermark_image_upload,
                    ),
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            # 水印图片透明度
            rx.cond(
                AdminState.whiteboard_watermark_image != "",
                rx.flex(
                    rx.text("水印图片透明度", size="3", weight="medium", color="var(--gray-11)", min_width="6rem"),
                    rx.slider(
                        default_value=[AdminState.whiteboard_watermark_opacity],
                        on_value_commit=AdminState.set_whiteboard_watermark_opacity,
                        min=0,
                        max=100,
                        step=5,
                        width="100%",
                    ),
                    rx.text(
                        f"{AdminState.whiteboard_watermark_opacity}%",
                        size="3",
                        color="var(--gray-11)",
                        min_width="3rem",
                        text_align="right",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
            ),
            rx.divider(),
            # 实时预览
            rx.heading("预览效果", size="4", weight="bold", color="var(--gray-11)"),
            rx.box(
                rx.cond(
                    AdminState.whiteboard_watermark != "",
                    rx.box(
                        rx.grid(
                            rx.foreach(
                                [i for i in range(4)],
                                lambda _: rx.text(
                                    AdminState.whiteboard_watermark,
                                    color=AdminState.watermark_text_color,
                                    weight="bold",
                                    style={
                                        "font_size": "2.5rem",
                                        "white_space": "nowrap",
                                        "pointer_events": "none",
                                        "user_select": "none",
                                        "transform": "rotate(-30deg)",
                                    },
                                ),
                            ),
                            columns="2",
                            spacing="9",
                            width="100%",
                            height="100%",
                            justify_items="center",
                            align_items="center",
                        ),
                        position="absolute",
                        top="-10vh",
                        left="-10vw",
                        width="120vw",
                        height="120vh",
                        overflow="hidden",
                        z_index="0",
                    ),
                ),
                rx.text(
                    "第 1 / 10 题",
                    size="4",
                    color="var(--gray-9)",
                    z_index="1",
                ),
                rx.text(
                    "这是一道示例题目，用于预览白板背景效果。",
                    size="5",
                    color="var(--gray-12)",
                    padding_top="4",
                    z_index="1",
                ),
                width="100%",
                height="20rem",
                border_radius="0.5rem",
                border="0.0625rem solid var(--gray-4)",
                position="relative",
                overflow="hidden",
                padding="4",
                style={
                    "background_color": AdminState.whiteboard_bg_color,
                },
            ),
            direction="column",
            spacing="4",
            width="100%",
            max_width="40rem",
            padding="4",
        ),
        value="settings",
    )


def admin() -> rx.Component:
    """后台管理页面 - 题库上传与管理."""
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("选择演讲题目", value="wellcome", padding_x="6"),
                rx.tabs.trigger("在线上传", value="text", padding_x="6"),
                rx.tabs.trigger("题库管理", value="manage"),
                rx.tabs.trigger("白板设置", value="settings"),
            ),
            _tab1_wellcome(),
            _tab2_upload(),
            _tab3_manage(),
            _tab4_settings(),
            default_value="wellcome",
            color_scheme="gray",
            variant="solid",
            on_change=AdminState.set_upload_tab,
            width="100%",
            padding_x="4",
            padding_y="8",
        ),
        width="100%",
    )
