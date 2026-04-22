# 选择题库页面

import reflex as rx

from LOBN_exam_speech_board_reflex.state import AppState


class WellcomeState(AppState):
    """State for the welcome page."""
    pass


def _format_time(timestamp) -> str:
    """Format timestamp to readable date string."""
    if not timestamp:
        return "未知"
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")


def _bank_card(bank: dict) -> rx.Component:
    """Render a single question bank card."""
    size_kb = bank.get("size_kb", "0")
    modified = bank.get("modified_str", "未知")
    return rx.card(
        rx.flex(
            rx.flex(
                rx.icon("book-open", size=28, color="var(--gray-11)"),
                rx.flex(
                    rx.text(
                        bank.get("name", "未命名题库"),
                        size="5",
                        weight="bold",
                        color="var(--gray-12)",
                    ),
                    rx.text(
                        f"{size_kb} KB",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.text(
                        f"修改时间: {modified}",
                        size="2",
                        color="var(--gray-8)",
                    ),
                    spacing="1",
                    direction="column",
                ),
                spacing="4",
            ),
            rx.button(
                rx.icon("play", size=16),
                "开始讲题",
                size="3",
                color_scheme="green",
                variant="solid",
                on_click=[
                    WellcomeState.load_bank(bank["filename"]),
                    rx.call_script("window.location.href = '/workspace'"),
                ],
                _hover={"bg": "var(--green-3)"},
            ),
            direction="column",
            width="100%",
            spacing="4",
        ),
        width="100%",
        size="3",
        variant="surface",
        _hover={"shadow": "lg"},
    )


def wellcome() -> rx.Component:
    """选择题库页面."""
    return rx.container(
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
            style={"padding_top": "6rem", "padding_bottom": "6rem"},
        ),
        rx.foreach(
            WellcomeState.bank_list,
            _bank_card,
        ),
        rx.cond(
            WellcomeState.bank_list == [],
            rx.flex(
                rx.text("暂无题库，请到后台上传题库文件"),
                justify_content="center",
                width="100%",
                style={"padding_top": "8rem", "padding_bottom": "8rem"},
            ),
        ),
        max_width="900px",
        width="100%",
        style={"padding_left": "4rem", "padding_right": "4rem", "padding_bottom": "8rem"},
    )
