# 编辑试题独立页面 - 可在新标签页打开，支持同时编辑多套题目

import reflex as rx

from LOBN_exam_speech_board_reflex.state import EditQuestionsState


def _edit_status_text() -> rx.Component:
    """编辑状态文本."""
    return rx.cond(
        EditQuestionsState.edit_status != "",
        rx.flex(
            rx.icon(
                rx.cond(
                    EditQuestionsState.edit_status.contains("失败"),
                    "alert-circle",
                    "check-circle",
                ),
                size=14,
                color=rx.cond(
                    EditQuestionsState.edit_status.contains("失败"),
                    "var(--red-9)",
                    "var(--green-9)",
                ),
            ),
            rx.text(
                EditQuestionsState.edit_status,
                size="2",
                color=rx.cond(
                    EditQuestionsState.edit_status.contains("失败"),
                    "var(--red-9)",
                    "var(--green-9)",
                ),
                weight="medium",
            ),
            spacing="1",
            align="center",
        ),
    )


def _option_row(opt) -> rx.Component:
    # 单选用 set_edited_answer，多选用 toggle_edited_answer
    on_click_fn = rx.cond(
        opt.to(dict)["question_type"] == "multiple",
        EditQuestionsState.toggle_edited_answer(opt.to(dict)["question_index"], opt.to(dict)["letter"]),
        EditQuestionsState.set_edited_answer(opt.to(dict)["question_index"], opt.to(dict)["letter"]),
    )
    return rx.flex(
        rx.button(
            opt.to(dict)["letter"],
            size="1",
            variant=rx.cond(opt.to(dict)["is_answer"].to(bool), "solid", "outline"),
            color_scheme=rx.cond(opt.to(dict)["is_answer"].to(bool), "green", "gray"),
            min_width="1.5rem",
            on_click=on_click_fn,
        ),
        rx.input(
            default_value=opt.to(dict)["text"],
            on_blur=EditQuestionsState.save_edited_option(
                opt.to(dict)["question_index"].to(int), opt.to(dict)["opt_index"].to(int),
            ),
            size="2",
            width="100%",
            variant="classic",
        ),
        spacing="2",
        align="center",
        width="100%",
    )


def _image_item(img: dict) -> rx.Component:
    return rx.flex(
        # 图片容器（点击预览大图）
        rx.box(
            rx.image(
                src=img.to(dict)["src"],
                width="100%",
                height="100%",
                object_fit="cover",
            ),
            on_click=EditQuestionsState.open_image_preview(img.to(dict)["src"]),
            width="5rem",
            height="5rem",
            border_radius="0.375rem",
            overflow="hidden",
            border="0.0625rem solid var(--gray-4)",
            cursor="pointer",
        ),
        # 下方操作按钮
        rx.hstack(
            rx.button(
                rx.icon("trash-2", size=10),
                "删除",
                size="1",
                variant="soft",
                color_scheme="red",
                on_click=EditQuestionsState.remove_image_from_question(img.to(dict)["question_index"], img.to(dict)["img_index"]),
            ),
            spacing="1",
            align="center",
            justify="center",
            width="100%",
        ),
        direction="column",
        spacing="1",
        align="center",
    )


def question_edit_card(item: dict[str, str | int | list[dict[str, str | bool | int]]], index: int) -> rx.Component:
    """单个题目编辑卡片."""
    # ---- 题型选择器 ----
    type_selector = rx.flex(
        rx.badge(
            item.to(dict)["display_id"],
            size="1",
            color_scheme="blue",
            variant="solid",
            weight="bold",
        ),
        rx.button(
            "单选",
            size="1",
            variant=rx.cond(item.to(dict).get("type", "single") == "single", "solid", "outline"),
            color_scheme=rx.cond(item.to(dict).get("type", "single") == "single", "blue", "gray"),
            on_click=EditQuestionsState.set_question_type(item.to(dict)["edit_index"], "single"),
        ),
        rx.button(
            "多选",
            size="1",
            variant=rx.cond(item.to(dict).get("type", "single") == "multiple", "solid", "outline"),
            color_scheme=rx.cond(item.to(dict).get("type", "single") == "multiple", "blue", "gray"),
            on_click=EditQuestionsState.set_question_type(item.to(dict)["edit_index"], "multiple"),
        ),
        rx.button(
            "判断",
            size="1",
            variant=rx.cond(item.to(dict).get("type", "single") == "judge", "solid", "outline"),
            color_scheme=rx.cond(item.to(dict).get("type", "single") == "judge", "blue", "gray"),
            on_click=EditQuestionsState.set_question_type(item.to(dict)["edit_index"], "judge"),
        ),
        spacing="2",
        align="center",
        width="100%",
    )

    # ---- 题干编辑 ----
    question_input = rx.flex(
        rx.text("题干：", size="2", weight="medium", min_width="3.5rem"),
        rx.text_area(
            default_value=item.to(dict).get("question", ""),
            on_blur=EditQuestionsState.save_edited_question_field(item.to(dict)["edit_index"], "question"),
            size="2",
            width="100%",
            min_height="3.75rem",
            variant="classic",
        ),
        spacing="2",
        align="start",
        width="100%",
    )

    # ---- 单选/多选：选项编辑（点击字母设置/切换答案） ----
    options_editor = rx.foreach(
        item.to(dict)["edit_options"].to(list),
        _option_row,
    )

    # ---- 判断题：√/× 按钮 ----
    judge_editor = rx.flex(
        rx.button(
            rx.icon("check", size=14),
            "正确",
            size="2",
            variant=rx.cond(
                item.to(dict)["answer_stripped"] == "A",
                "solid",
                "outline",
            ),
            color_scheme=rx.cond(item.to(dict)["answer_stripped"].to(str) == "A", "green", "gray"),
            on_click=EditQuestionsState.set_edited_answer(item.to(dict)["edit_index"], "A"),
        ),
        rx.button(
            rx.icon("x", size=14),
            "错误",
            size="2",
            variant=rx.cond(
                item.to(dict)["answer_stripped"] == "B",
                "solid",
                "outline",
            ),
            color_scheme=rx.cond(
                item.to(dict)["answer_stripped"] == "B",
                "red",
                "gray",
            ),
            on_click=EditQuestionsState.set_edited_answer(item.to(dict)["edit_index"], "B"),
        ),
        spacing="3",
        align="center",
        width="100%",
    )

    # ---- 解析编辑 ----
    explanation_input = rx.flex(
        rx.text("解析：", size="2", weight="medium", min_width="3.5rem"),
        rx.text_area(
            default_value=item.to(dict).get("explanation", ""),
            on_blur=EditQuestionsState.save_edited_question_field(item.to(dict)["edit_index"], "explanation"),
            size="2",
            width="100%",
            min_height="2.5rem",
            variant="classic",
        ),
        spacing="2",
        align="start",
        width="100%",
    )

    # ---- 图片管理 ----
    images_section: rx.Component = rx.flex(
        rx.text("图片：", size="2", weight="medium", min_width="3.5rem"),
        # 现有图片缩略图
        rx.foreach(
            item.to(dict)["edit_images"].to(list),
            _image_item,
        ),
        # 上传按钮（打开对话框）
        rx.button(
            rx.icon("plus", size=16),
            size="1",
            variant="outline",
            color_scheme="blue",
            on_click=EditQuestionsState.open_upload_dialog(item.to(dict)["edit_index"]),
        ),
        spacing="2",
        align="center",
        width="100%",
        wrap="wrap",
    )

    return rx.card(
        rx.flex(
            type_selector,
            question_input,
            # 根据题型显示不同选项UI
            rx.cond(
                item.to(dict).get("type", "single") == "judge",
                judge_editor,
                options_editor,
            ),
            explanation_input,
            images_section,
            direction="column",
            spacing="3",
            width="100%",
        ),
        width="100%",
        size="1",
        variant="surface",
    )


def _empty_state() -> rx.Component:
    """未加载题库时的空状态提示."""
    return rx.flex(
        rx.icon("alert-circle", size=48, color="var(--gray-6)"),
        rx.text("未指定题库", size="5", color="var(--gray-9)"),
        rx.text(
            "请从管理页面点击「编辑试题」按钮进入",
            size="2",
            color="var(--gray-7)",
        ),
        rx.link(
            rx.button("返回管理页面", size="3", color_scheme="blue"),
            href="/",
        ),
        direction="column",
        align="center",
        spacing="4",
        padding_y="8rem",
    )


def _image_preview_dialog() -> rx.Component:
    """图片预览对话框."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("查看图片"),
            rx.box(
                rx.image(
                    src=EditQuestionsState.image_preview_src,
                    width="100%",
                    max_height="70vh",
                    object_fit="contain",
                ),
                width="100%",
                display="flex",
                justify_content="center",
            ),
            rx.flex(
                rx.button(
                    "关闭",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EditQuestionsState.close_image_preview,
                ),
                justify="center",
                padding_top="4",
            ),
            max_width="90vw",
            max_height="90vh",
        ),
        open=EditQuestionsState.image_preview_open,
        on_open_change=EditQuestionsState.close_image_preview,
    )


def _upload_dialog() -> rx.Component:
    """图片上传对话框."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("上传图片"),
            rx.dialog.description("拖拽图片到下方区域或点击选择文件"),
            rx.upload.root(
                rx.box(
                    rx.icon("upload", size=32, color="var(--gray-6)"),
                    rx.text("点击或拖拽上传图片", size="2", color="var(--gray-8)"),
                    width="100%",
                    height="10rem",
                    border="0.0625rem dashed var(--gray-5)",
                    border_radius="0.375rem",
                    display="flex",
                    flex_direction="column",
                    align_items="center",
                    justify_content="center",
                    gap="0.5rem",
                    _hover={"border_color": "var(--blue-7)", "bg": "var(--gray-2)"},
                ),
                id="question_image_upload",
                multiple=False,
                accept={
                    "image/png": [".png"],
                    "image/jpeg": [".jpg", ".jpeg"],
                    "image/gif": [".gif"],
                    "image/webp": [".webp"],
                },
                on_drop=EditQuestionsState.handle_upload_dialog_drop,
            ),
            rx.flex(
                rx.button(
                    "取消",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EditQuestionsState.close_upload_dialog,
                ),
                spacing="3",
                justify="end",
                padding_top="4",
            ),
        ),
        open=EditQuestionsState.upload_dialog_open,
        on_open_change=EditQuestionsState.close_upload_dialog,
    )


def edit_questions() -> rx.Component:
    """编辑试题独立页面 - 可在新标签页打开."""
    return rx.container(
        rx.flex(
            # 顶部工具栏
            rx.flex(
                rx.link(
                    rx.button(
                        rx.icon("arrow-left", size=18),
                        "返回管理",
                        size="2",
                        variant="soft",
                        color_scheme="gray",
                    ),
                    href="/",
                ),
                rx.heading(
                    f"编辑试题 - {EditQuestionsState.editing_bank_name}",
                    size="5",
                ),
                rx.spacer(),
                _edit_status_text(),
                align="center",
                width="100%",
            ),
            rx.text(
                "编辑后失焦自动保存，关闭窗口结束编辑。",
                size="2",
                color="var(--gray-9)",
            ),
            # 题目列表 / 空状态
            rx.cond(
                EditQuestionsState.editing_bank_filename != "",
                rx.flex(
                    rx.foreach(
                        EditQuestionsState.editing_questions_formatted,
                        lambda item, index: question_edit_card(item, index),
                    ),
                    direction="column",
                    spacing="3",
                    width="100%",
                    overflow_y="auto",
                    padding_y="2",
                ),
                _empty_state(),
            ),
            _upload_dialog(),
            _image_preview_dialog(),
            direction="column",
            spacing="4",
            width="100%",
            padding="6",
        ),
        style={"padding": "0", "max_width": "100vw", "min_height": "100vh"},
    )
