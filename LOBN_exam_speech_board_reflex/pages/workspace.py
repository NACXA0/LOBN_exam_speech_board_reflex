# 讲题主页

import reflex as rx

from LOBN_exam_speech_board_reflex.state import AppState


class WorkspaceState(AppState):
    """State for the workspace page."""


def _render_image(img_src: str) -> rx.Component:
    """从base64编码或路径渲染图像"""
    return rx.cond(
        img_src == "",
        rx.fragment(),
        rx.image(
            src=rx.cond(
                img_src.startswith("data:") | img_src.startswith("http://") | img_src.startswith("https://"),
                img_src,
                f"/assets/{img_src}",
            ),
            width="100%",
            max_width="31.25rem",
            radius="medium",
        ),
    )


def _question_header() -> rx.Component:
    """显示问题编号和类型标识。"""
    q_type = WorkspaceState.current_question_type
    type_label = rx.cond(q_type == "multiple", "多选题", rx.cond(q_type == "judge", "判断题", "单选题"))
    type_color = rx.cond(q_type == "multiple", "orange", rx.cond(q_type == "judge", "green", "blue"))
    return rx.flex(
        rx.text(
            f"{WorkspaceState.current_index + 1} / {WorkspaceState.total_questions}",
            size="4",
            color="var(--gray-9)",
        ),
        rx.badge(
            type_label,
            color_scheme=type_color,
            variant="solid",
            size="2",
        ),
        spacing="3",
        align="center",
    )


def _question_text() -> rx.Component:
    """Render question text with images."""
    return rx.flex(
        rx.cond(
            WorkspaceState.current_question_text != "",
            rx.text(
                WorkspaceState.current_question_text,
                size="7",
                weight="medium",
                color="var(--gray-12)",
                line_height="1.7",
            ),
        ),
        rx.foreach(
            WorkspaceState.current_question_images_list.to(list),
            lambda img: _render_image(img.to(dict)["src"].to(str)),
        ),
        direction="column",
        spacing="4",
        width="100%",
        max_width="50rem",
    )


def _option_item(option_data: dict) -> rx.Component:
    """Single option card with adaptive height."""
    option_letter = option_data["letter"]
    option_text = option_data["text"]
    index = option_data["index"]

    is_selected = WorkspaceState.selected_option == index
    is_correct = option_letter == WorkspaceState.current_question_answer

    bg_color = rx.cond(
        is_selected & WorkspaceState.show_explanation,
        rx.cond(is_correct, "var(--green-3)", "var(--red-3)"),
        rx.cond(is_selected, "var(--green-3)", "#fafaf9"),
    )

    border_color = rx.cond(
        is_selected & WorkspaceState.show_explanation,
        rx.cond(is_correct, "var(--green-7)", "var(--red-7)"),
        rx.cond(is_selected, "var(--green-7)", "var(--gray-5)"),
    )

    return rx.button(
        rx.flex(
            rx.box(
                rx.text(option_letter, size="2", weight="bold", color="var(--gray-11)"),
                width="1.625rem",
                height="1.625rem",
                display="flex",
                align_items="center",
                justify_content="center",
                background_color="var(--gray-3)",
                radius="small",
            ),
            rx.text(
                option_text,
                size="3",
                color="var(--gray-12)",
                flex="1",
                line_height="1.5",
                white_space="normal",
                word_break="break-word",
            ),
            rx.cond(
                is_selected & WorkspaceState.show_explanation,
                rx.icon(
                    rx.cond(is_correct, "check-circle", "x-circle"),
                    size=32,
                    color=rx.cond(is_correct, "var(--green-9)", "var(--red-9)"),
                )
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        width="100%",
        variant="ghost",
        background_color=bg_color,
        border=f"0.0625rem solid {border_color}",
        radius="medium",
        align_self="stretch",
        cursor="pointer",
        padding_y="2",
        padding_x="3",
        on_click=WorkspaceState.select_option(index),
        _hover={"bg": "var(--gray-3)"},
        transition="all 0.15s ease",
        style={
            "justify_content": "flex-start",
            "text_align": "left",
            "height": "auto",
            "min_height": "2.5rem",
        },
    )


def _options_area() -> rx.Component:
    """Render answer options as card list."""
    options_with_letters = WorkspaceState.options_with_letters
    return rx.fragment(
        rx.cond(
            options_with_letters.length() > 0,
            rx.flex(
                rx.foreach(options_with_letters, _option_item),
                direction="column",
                spacing="2",
                width="100%",
            ),
        ),
    )


def _explanation_area() -> rx.Component:
    """Render explanation card."""
    return rx.fragment(
        rx.cond(
            WorkspaceState.show_explanation & (WorkspaceState.current_question_explanation != ""),
            rx.flex(
                rx.flex(
                    rx.text("答案解析", size="3", weight="bold", color="var(--green-10)"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    WorkspaceState.current_question_explanation,
                    size="3",
                    color="var(--gray-11)",
                    line_height="1.6",
                ),
                direction="column",
                spacing="2",
                width="100%",
                padding="3",
                background_color="var(--green-2)",
                border="0.0625rem solid var(--green-5)",
                radius="medium",
            ),
        ),
    )


def _speech_explanation_area() -> rx.Component:
    """讲题布局专用解析卡片 - 始终显示，不受show_explanation控制。"""
    return rx.fragment(
        rx.cond(
            WorkspaceState.current_question_explanation != "",
            rx.flex(
                rx.flex(
                    rx.text("答案解析", size="3", weight="bold", color="var(--green-10)"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    WorkspaceState.current_question_explanation,
                    size="3",
                    color="var(--gray-11)",
                    line_height="1.6",
                ),
                direction="column",
                spacing="2",
                width="100%",
                padding="3",
                background_color="var(--green-2)",
                border="0.0625rem solid var(--green-5)",
                radius="medium",
            ),
        ),
    )


def _speech_area() -> rx.Component:
    """Render speech script card."""
    return rx.fragment(
        rx.cond(
            WorkspaceState.current_question_speech != "",
            rx.flex(
                rx.flex(
                    rx.icon("file-text", size=14, color="var(--blue-9)"),
                    rx.text("演讲稿", size="3", weight="bold", color="var(--blue-10)"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    WorkspaceState.current_question_speech,
                    size="3",
                    color="var(--gray-11)",
                    line_height="1.7",
                    white_space="pre-wrap",
                ),
                direction="column",
                spacing="2",
                width="100%",
                padding="3",
                background_color="var(--blue-2)",
                border="0.0625rem solid var(--blue-5)",
                radius="medium",
            ),
        ),
    )


def _navigation() -> rx.Component:
    """呈现轻量级的导航统计数据。"""
    stats = WorkspaceState.answer_statistics
    return rx.fragment(
        rx.cond(
            (WorkspaceState.current_bank_name != "") & (WorkspaceState.total_questions > 0),
            rx.flex(
                rx.badge(
                    rx.text(f"{stats.to(dict)['correct']}/{stats.to(dict)['total']}", size="1", weight="bold"),
                    color_scheme=rx.cond(stats["is_good"], "green", "yellow"),
                    variant="soft",
                ),
                rx.text(
                    f"{stats.to(dict)['accuracy']}",
                    size="1",
                    color="var(--gray-9)",
                ),
                spacing="2",
                align="center",
            ),
            rx.fragment(),
        ),
    )


def _toolbar() -> rx.Component:
    """Render lightweight top toolbar."""
    return rx.flex(
        rx.button(
            rx.icon("arrow-left", size=32),
            size="4",
            variant="ghost",
            color_scheme="gray",
            on_click=rx.redirect("/"),
            tooltip="返回选择题库",
            tooltip_shade="3",
        ),
        rx.text(
            WorkspaceState.current_bank_name,
            size="6",
            weight="medium",
            color="var(--gray-10)",
        ),
        rx.spacer(),
        # 布局切换下拉菜单
        rx.select.root(
            rx.select.trigger(
                variant="surface",
                size="3",
                placeholder="选择布局",
            ),
            rx.select.content(
                rx.select.item("讲题布局", value="speech"),
                rx.select.item("经典布局", value="classic"),
            ),
            value=WorkspaceState.workspace_layout,
            on_change=WorkspaceState.set_workspace_layout,
        ),
        rx.button(
            rx.icon("rotate-ccw", size=32),
            size="4",
            variant="ghost",
            color_scheme="gray",
            on_click=WorkspaceState.reset_quiz,
            tooltip="重置",
            tooltip_shade="3",
        ),
        spacing="3",
        align="center",
        padding_x="4",
        padding_y="2",
    )


def _empty_state() -> rx.Component:
    """Render empty state when no bank is loaded."""
    return rx.flex(
        rx.flex(
            rx.icon("book-open", size=64, color="var(--gray-6)", weight="light"),
            rx.text("请先选择题库", size="5", weight="medium", color="var(--gray-9)"),
            rx.text("返回首页选择题库开始讲题", size="3", color="var(--gray-7)"),
            rx.button(
                rx.icon("arrow-left", size=32),
                "返回首页",
                size="3",
                variant="solid",
                on_click=rx.redirect("/"),
            ),
            direction="column",
            align="center",
            spacing="4",
        ),
        rx.spacer(),
        rx.spacer(),
        width="100%",
        height="60vh",
    )


# ============================================================
# 经典布局（旧布局）
# ============================================================

def _left_column() -> rx.Component:
    """Left column: question header + text, auto-centered when short."""
    return rx.flex(
        rx.spacer(),
        rx.flex(
            rx.cond(
                WorkspaceState.current_bank_name != "",
                _question_header(),
                rx.text("请先选择题库", size="4", color="var(--gray-9)"),
            ),
            _question_text(),
            direction="column",
            spacing="4",
            width="100%",
            max_width="50rem",
        ),
        rx.spacer(),
        direction="column",
        align="center",
        flex="1",
        min_width="0",
        padding="6",
        overflow_y="auto",
        height="100%",
    )


def _right_column() -> rx.Component:
    """Right column: scrollable content + fixed bottom navigation."""
    return rx.flex(
        # Scrollable content area
        rx.flex(
            _options_area(),
            _explanation_area(),
            direction="column",
            spacing="3",
            width="100%",
            flex="1",
            overflow_y="auto",
            min_height="0",
        ),
        # Fixed bottom navigation
        rx.flex(
            rx.divider(color="var(--gray-5)"),
            _navigation(),
            direction="column",
            spacing="2",
            width="100%",
            padding_top="2",
        ),
        direction="column",
        spacing="0",
        width="100%",
        height="100%",
    )


def _classic_layout() -> rx.Component:
    """经典双栏布局：左侧题干，右侧选项+解析。"""
    return rx.flex(
        # Left card
        rx.box(
            _left_column(),
            background_color=WorkspaceState.whiteboard_bg_color,
            style={"border_radius": "0.75rem"},
            box_shadow="0 0.0625rem 0.25rem rgba(0,0,0,0.04)",
            flex="1",
            min_width="0",
            overflow="hidden",
        ),
        # Right card (collapsible)
        rx.cond(
            WorkspaceState.right_panel_collapsed,
            rx.fragment(),
            rx.box(
                _right_column(),
                background_color=WorkspaceState.whiteboard_bg_color,
                style={"border_radius": "0.75rem"},
                box_shadow="0 0.0625rem 0.25rem rgba(0,0,0,0.04)",
                width="26rem",
                min_width="22rem",
                max_width="30rem",
                overflow="hidden",
            ),
        ),
        direction="row",
        spacing="4",
        width="100%",
        flex="1",
        overflow="hidden",
        padding="4",
        background_color="#f2f2f0",
    )


# ============================================================
# 讲题布局（新默认布局）
# ============================================================

def _right_panel_tab_bar() -> rx.Component:
    """右侧面板三段式Tab控制栏 + 常驻正确答案。"""
    return rx.flex(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("解析", value="explanation"),
                rx.tabs.trigger("各半", value="half"),
                rx.tabs.trigger("演讲稿", value="speech"),
            ),
            default_value=WorkspaceState.right_panel_tab,
            on_change=WorkspaceState.set_right_panel_tab,
            style={"flex": "1"},
        ),
        # 右侧常驻正确答案
        rx.cond(
            WorkspaceState.current_bank_name != "",
            rx.badge(
                rx.cond(WorkspaceState.current_question_answer != "", WorkspaceState.current_question_answer, '无'),
                color_scheme="green",
                variant="solid",
                size="3",
                radius="full",
            ),
        ),
        spacing="2",
        align="center",
        width="100%",
    )


def _speech_right_column() -> rx.Component:
    """讲题布局右侧：解析+演讲稿，Tab控制显示比例。"""
    # 根据tab状态决定解析和演讲稿的flex比例
    # explanation: 解析flex=1, 演讲稿flex=0
    # half: 解析flex=1, 演讲稿flex=1
    # speech: 解析flex=0, 演讲稿flex=1
    explanation_flex = rx.cond(
        WorkspaceState.right_panel_tab == "explanation", "1",
        rx.cond(
            WorkspaceState.right_panel_tab == "half", "1",
            "0",
        ),
    )
    speech_flex = rx.cond(
        WorkspaceState.right_panel_tab == "speech", "1",
        rx.cond(
            WorkspaceState.right_panel_tab == "half", "1",
            "0",
        ),
    )

    # 解析区overflow
    explanation_overflow = rx.cond(
        WorkspaceState.right_panel_tab == "explanation",
        "auto",
        rx.cond(
            WorkspaceState.right_panel_tab == "half",
            "auto",
            "hidden",
        ),
    )
    # 演讲稿区overflow
    speech_overflow = rx.cond(
        WorkspaceState.right_panel_tab == "speech",
        "auto",
        rx.cond(
            WorkspaceState.right_panel_tab == "half",
            "auto",
            "hidden",
        ),
    )

    return rx.flex(
        # Tab控制栏
        _right_panel_tab_bar(),
        # 解析区（讲题布局始终显示）
        rx.flex(
            _speech_explanation_area(),
            direction="column",
            width="100%",
            flex=explanation_flex,
            overflow_y=explanation_overflow,
            min_height="0",
            padding_top="2",
        ),
        # 分隔线（各半和演讲稿模式下显示）
        rx.cond(
            (WorkspaceState.right_panel_tab == "half") | (WorkspaceState.right_panel_tab == "speech"),
            rx.divider(color="var(--gray-4)"),
        ),
        # 演讲稿区
        rx.flex(
            _speech_area(),
            direction="column",
            width="100%",
            flex=speech_flex,
            overflow_y=speech_overflow,
            min_height="0",
            padding_top="2",
        ),
        # 底部导航
        rx.flex(
            rx.divider(color="var(--gray-5)"),
            _navigation(),
            direction="column",
            spacing="2",
            width="100%",
            padding_top="2",
        ),
        direction="column",
        spacing="1",
        width="100%",
        height="100%",
    )


def _speech_layout() -> rx.Component:
    """讲题布局：左侧2/3题干+选项，右侧1/3解析+演讲稿。"""
    return rx.flex(
        # 左侧卡片：题干 + 选项 (2/3)
        rx.box(
            rx.flex(
                # 题号+题型
                rx.cond(
                    WorkspaceState.current_bank_name != "",
                    _question_header(),
                    rx.text("请先选择题库", size="4", color="var(--gray-9)"),
                ),
                # 题干
                _question_text(),
                # 选项
                _options_area(),
                direction="column",
                spacing="4",
                width="100%",
                max_width="50rem",
            ),
            background_color=WorkspaceState.whiteboard_bg_color,
            style={"border_radius": "0.75rem"},
            box_shadow="0 0.0625rem 0.25rem rgba(0,0,0,0.04)",
            flex="2",
            min_width="0",
            overflow="auto",
            padding="6",
            position="relative",
        ),
        # 右侧卡片：解析 + 演讲稿 (1/3)
        rx.box(
            _speech_right_column(),
            background_color=WorkspaceState.whiteboard_bg_color,
            style={"border_radius": "0.75rem"},
            box_shadow="0 0.0625rem 0.25rem rgba(0,0,0,0.04)",
            flex="1",
            min_width="18rem",
            max_width="30rem",
            overflow="hidden",
            padding="4",
        ),
        direction="row",
        spacing="4",
        width="100%",
        flex="1",
        overflow="hidden",
        padding="4",
        background_color="#f2f2f0",
    )


def _question_switcher() -> rx.Component:
    """Bottom-right fixed question switcher - lightweight."""
    return rx.cond(
        WorkspaceState.current_bank_name != "",
        rx.box(
            rx.flex(
                rx.button(
                    rx.icon("skip-back", size=32),
                    size="4",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=WorkspaceState.go_to_first_question,
                    tooltip="跳转到第一题",
                    tooltip_shade="3",
                ),
                rx.button(
                    rx.icon("chevrons-left", size=32),
                    size="4",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=WorkspaceState.prev_question,
                    disabled=WorkspaceState.current_index <= 0,
                    tooltip="上一题",
                    tooltip_shade="3",
                ),
                rx.text(
                    f"{WorkspaceState.current_index + 1} / {WorkspaceState.total_questions}",
                    size="6",
                    color="var(--gray-8)",
                    weight="medium",
                ),
                rx.button(
                    rx.icon("chevrons-right", size=32),
                    size="4",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=WorkspaceState.next_question,
                    disabled=WorkspaceState.current_index >= WorkspaceState.total_questions - 1,
                    tooltip="下一题",
                    tooltip_shade="3",
                ),
                rx.button(
                    rx.icon("skip-forward", size=32),
                    size="4",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=WorkspaceState.go_to_last_question,
                    tooltip="跳转到最后一题",
                    tooltip_shade="3",
                ),
                spacing="5",
                align="center",
            ),
            position="fixed",
            bottom="1rem",
            right="1rem",
            background_color="var(--color-panel)",
            border="0.0625rem solid var(--gray-4)",
            radius="medium",
            padding="3",
            shadow="medium",
            z_index="1000",
        ),
    )


def _watermark_image_overlay() -> rx.Component:
    """水印图片覆盖层 - 页面正中间显示，可调透明度。"""
    return rx.cond(
        WorkspaceState.whiteboard_watermark_image != "",
        rx.box(
            rx.image(
                src=rx.cond(
                    WorkspaceState.whiteboard_watermark_image.startswith("data:") | WorkspaceState.whiteboard_watermark_image.startswith("http://") | WorkspaceState.whiteboard_watermark_image.startswith("https://"),
                    WorkspaceState.whiteboard_watermark_image,
                    f"/assets/{WorkspaceState.whiteboard_watermark_image}",
                ),
                width="auto",
                height="auto",
                max_width="24rem",
                max_height="24rem",
                object_fit="contain",
                opacity=WorkspaceState.watermark_opacity_css,
            ),
            position="fixed",
            top="50%",
            left="50%",
            transform="translate(-50%, -50%)",
            z_index="0",
            pointer_events="none",
            user_select="none",
        ),
    )


def workspace() -> rx.Component:
    """Main workspace page - adaptive two-column layout with soft neutral theme."""
    return rx.box(
        # Layer 0: Background color (bottommost)
        # Applied via _left_column background_color

        # Layer 1: Main content (interactive)
        rx.box(
            rx.flex(
                # Top toolbar
                _toolbar(),
                # Main content area
                rx.flex(
                    rx.cond(
                        WorkspaceState.current_bank == {},
                        _empty_state(),
                        # 根据布局模式切换
                        rx.cond(
                            WorkspaceState.workspace_layout == "speech",
                            _speech_layout(),
                            _classic_layout(),
                        ),
                    ),
                    flex="1",
                    overflow="hidden",
                ),
                direction="column",
                width="100%",
                height="100vh",
                background_color="#f2f2f0",
            ),
            # Question switcher
            _question_switcher(),
            # 水印图片覆盖层（仅在讲题布局时显示）
            rx.cond(
                WorkspaceState.workspace_layout == "speech",
                _watermark_image_overlay(),
            ),
            position="relative",
            z_index="0",
            width="100%",
            height="100%",
        ),

        # Layer 2: Watermark overlay (above content, clicks pass through)
        rx.cond(
            WorkspaceState.whiteboard_watermark != "",
            rx.box(
                rx.grid(
                    rx.foreach(
                        [i for i in range(6)],
                        lambda _: rx.text(
                            WorkspaceState.whiteboard_watermark,
                            color=WorkspaceState.watermark_text_color,
                            weight="bold",
                            style={
                                "font_size": "3rem",
                                "white_space": "nowrap",
                                "pointer_events": "none",
                                "user_select": "none",
                                "transform": "rotate(-30deg)",
                            },
                        ),
                    ),
                    columns="3",
                    spacing="9",
                    width="100%",
                    height="100%",
                    justify_items="center",
                    align_items="center",
                ),
                position="fixed",
                top="-10vh",
                left="-10vw",
                width="120vw",
                height="120vh",
                overflow="hidden",
                z_index="1",
                pointer_events="none",
            ),
        ),
        # Outer box: background color only (Layer 0)
        padding="0",
        max_width="100vw",
        height="100vh"

    )
