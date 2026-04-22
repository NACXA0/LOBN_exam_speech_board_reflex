# 讲题主页

import reflex as rx

from LOBN_exam_speech_board_reflex.state import AppState


class WorkspaceState(AppState):
    """State for the workspace page."""


def _render_image(img_src: str) -> rx.Component:
    """Render an image from base64 or path."""
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
            max_width="600px",
            radius="medium",
        ),
    )


def _question_area() -> rx.Component:
    """Render the question display area."""
    return rx.fragment(
        rx.cond(
            WorkspaceState.current_bank_name != "",
            rx.flex(
                # Question number
                rx.badge(
                    rx.text(
                        f"第 {WorkspaceState.current_question_id} 题",
                        size="3",
                        weight="bold",
                    ),
                    color_scheme="gray",
                    variant="outline",
                    padding_x="3",
                    padding_y="1",
                ),
                # Progress
                rx.text(
                    f"{WorkspaceState.current_index + 1} / {WorkspaceState.total_questions}",
                    size="3",
                    color="var(--gray-9)",
                ),
                width="100%",
                justify="between",
            ),
            rx.text("请先选择题库", size="4", color="var(--gray-9)"),
        ),
    )


def _question_text() -> rx.Component:
    """Render question text."""
    return rx.fragment(
        rx.cond(
            WorkspaceState.current_question_text != "",
            rx.text(
                WorkspaceState.current_question_text,
                size="5",
                weight="medium",
                color="var(--gray-12)",
                line_height="1.6",
                padding_y="4",
            ),
        ),
        # Render question images
        rx.foreach(
            WorkspaceState.current_question_images,
            lambda img: _render_image(img),
        ),
    )


def _options_area() -> rx.Component:
    """Render answer options."""
    options_with_letters = WorkspaceState.options_with_letters
    correct_answer = WorkspaceState.current_question_answer

    def _option_item(option_data: dict) -> rx.Component:
        """Single option component with option letter and text."""
        option_letter = option_data["letter"]
        option_text = option_data["text"]
        index = option_data["index"]
        
        is_selected = WorkspaceState.selected_option == index
        is_correct = option_letter == correct_answer

        # 根据状态确定背景颜色
        bg_color = rx.cond(
            is_selected & WorkspaceState.show_explanation,
            rx.cond(
                is_correct,
                "var(--green-4)",  # Correct: green
                "var(--red-4)",  # Wrong: red
            ),
            rx.cond(
                is_selected,
                "var(--green-3)",
                "var(--gray-3)",
            ),
        )

        def get_border():
            return rx.cond(
                is_selected & WorkspaceState.show_explanation,
                rx.cond(
                    is_correct,
                    "2px solid var(--green-6)",
                    "2px solid var(--red-6)",
                ),
                rx.cond(
                    is_selected,
                    "2px solid var(--green-5)",
                    "2px solid var(--gray-4)",
                ),
            )

        return rx.button(
            rx.flex(
                rx.badge(
                    rx.text(option_letter, size="3", weight="bold"),
                    size="2",
                    color_scheme="gray",
                    variant="outline",
                    width="32px",
                    height="32px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text(
                    option_text,
                    size="4",
                    color="var(--gray-12)",
                    flex="1",
                ),
                rx.cond(
                    is_selected & WorkspaceState.show_explanation,
                    rx.icon(
                        rx.cond(is_correct, "check-circle", "x-circle"),
                        size=20,
                        color=rx.cond(is_correct, "var(--green-8)", "var(--red-8)"),
                    )
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            width="100%",
            size="4",
            variant="surface",
            bg=bg_color,
            border=get_border(),
            align_self="stretch",
            cursor="pointer",
            on_click=WorkspaceState.select_option(index),
            _hover={"bg": "var(--gray-3)"},
        )

    return rx.fragment(
        rx.cond(
            options_with_letters.length() > 0,
            rx.flex(
                rx.foreach(options_with_letters, _option_item),
                direction="column",
                spacing="3",
                width="100%",
            ),
        ),
    )


def _explanation_area() -> rx.Component:
    """Render answer explanation."""
    return rx.fragment(
        rx.cond(
            WorkspaceState.show_explanation & (WorkspaceState.current_question_explanation != ""),
            rx.card(
                rx.flex(
                    rx.text("答案解析", size="4", weight="bold", color="var(--gray-12)"),
                    rx.divider(),
                    rx.text(
                        WorkspaceState.current_question_explanation,
                        size="3",
                        color="var(--gray-11)",
                        line_height="1.6",
                    ),
                    rx.foreach(
                        WorkspaceState.current_question_images,
                        lambda img: _render_image(img),
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
    )


def _navigation() -> rx.Component:
    """Render navigation buttons."""
    stats: dict[str, str | int] = WorkspaceState.answer_statistics
    return rx.fragment(
        rx.cond(
            (WorkspaceState.current_bank_name != "") & (WorkspaceState.total_questions > 0),
            rx.flex(
                # Statistics display
                rx.card(
                    rx.flex(
                        rx.badge(
                            rx.text(f"答题：{stats.to(dict)['correct']}/{stats.to(dict)['total']}" , size="3", weight="bold"),
                            color_scheme=rx.cond(stats["is_good"], "green", "yellow"),
                            variant="solid",
                        ),
                        rx.text(
                            f"正确率：{stats.to(dict)['accuracy']}",
                            size="3",
                            color="var(--gray-11)",
                        ),
                        spacing="2",
                    ),
                    width="150px",
                    size="2",
                    variant="surface",
                ),
                rx.spacer(),
                # Navigation buttons
                rx.flex(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        "上一题",
                        size="3",
                        variant="outline",
                        on_click=WorkspaceState.prev_question,
                        disabled=WorkspaceState.current_index <= 0,
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("arrow-right", size=20),
                        "下一题",
                        size="3",
                        color_scheme="blue",
                        variant="solid",
                        on_click=WorkspaceState.next_question,
                        disabled=WorkspaceState.current_index >= WorkspaceState.total_questions - 1,
                    ),
                    spacing="4",
                    width="100%",
                    justify="center",
                ),
                direction="column",
                spacing="2",
            ),
            rx.fragment(),
        ),
    )


def _toolbar() -> rx.Component:
    """Render the toolbar with navigation controls."""
    return rx.flex(
        # Back button
        rx.button(
            rx.icon("arrow-left", size=20),
            size="3",
            variant="soft",
            color_scheme="gray",
            on_click=rx.call_script("window.location.href = '/'"),
            tooltip="返回选择题库",
            tooltip_shade="3",
        ),
        rx.spacer(),

        # Bank name
        rx.text(
            WorkspaceState.current_bank_name,
            size="3",
            weight="medium",
            color="var(--gray-11)",
        ),

        rx.spacer(),

        # Reset
        rx.button(
            rx.icon("rotate-ccw", size=20),
            size="3",
            variant="soft",
            color_scheme="gray",
            on_click=WorkspaceState.reset_quiz,
            tooltip="重置",
            tooltip_shade="3",
        ),

        spacing="3",
    )


def _empty_state() -> rx.Component:
    """Render empty state when no bank is loaded."""
    return rx.flex(
        rx.flex(
            rx.icon("book-open", size=64, color="var(--gray-6)", weight="light"),
            rx.text("请先选择题库", size="5", weight="medium", color="var(--gray-9)"),
            rx.text("返回首页选择题库开始讲题", size="3", color="var(--gray-7)"),
            rx.button(
                rx.icon("arrow-left", size=16),
                "返回首页",
                size="3",
                variant="solid",
                on_click=rx.call_script("window.location.href = '/'"),
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


def workspace() -> rx.Component:
    """讲题主页 - 题目展示和交互."""
    return rx.container(
        rx.flex(
            rx.flex(
                _toolbar(),
                direction="column",
                spacing="2",
                width="100%",
                padding="4",
                bg="var(--gray-2)",
                border_bottom="1px solid var(--gray-4)",
            ),
            rx.flex(
                rx.cond(
                    WorkspaceState.current_bank == {},
                    _empty_state(),
                    rx.flex(
                        rx.flex(
                            _question_area(),
                            _question_text(),
                            rx.divider(),
                            _options_area(),
                            _explanation_area(),
                            rx.divider(),
                            _navigation(),
                            direction="column",
                            spacing="4",
                            width="100%",
                            max_width="800px",
                            padding="6",
                        ),
                        rx.spacer(),
                        rx.spacer(),
                        flex="1",
                        overflow_y="auto",
                    ),
                ),
                flex="1",
                overflow="hidden",
            ),
            direction="column",
            spacing="4",
            width="100%",
            height="100vh",
        ),
        style={
            "padding": "0",
            "max_width": "100vw",
            "height": "100vh",
        },
    )
