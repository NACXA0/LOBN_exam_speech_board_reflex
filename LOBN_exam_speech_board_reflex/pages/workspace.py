# 讲题主页

import reflex as rx

from LOBN_exam_speech_board_reflex.state import AppState


class WorkspaceState(AppState):
    """State for the workspace page."""
    # Canvas state
    canvas_data: str = ""
    pen_color: str = "#000000"
    pen_size: int = 3
    eraser_mode: bool = False

    # Image data for current question
    _image_cache: dict = {}

    def clear_canvas(self):
        """Clear the drawing canvas."""
        self.canvas_data = ""

    def set_pen_color(self, color: str):
        """Set pen color."""
        self.pen_color = color

    def set_pen_size(self, size: int):
        """Set pen size."""
        self.pen_size = size

    def toggle_eraser(self):
        """Toggle eraser mode."""
        self.eraser_mode = not self.eraser_mode

    def set_canvas_data(self, data: str):
        """Set canvas data from JavaScript."""
        self.canvas_data = data

    def export_canvas(self) -> str:
        """Export canvas as image."""
        return self.canvas_data


def _get_question() -> dict:
    """Get current question from state."""
    questions = WorkspaceState.current_bank.get("questions", [])
    idx = WorkspaceState.current_index
    if 0 <= idx < len(questions):
        return questions[idx]
    return {}


def _get_bank_name() -> str:
    """Get current bank name."""
    return WorkspaceState.current_bank.get("name", "未命名题库")


def _get_total() -> int:
    """Get total question count."""
    return WorkspaceState.current_bank.get("total_questions", 0)


def _render_image(img_src: str) -> rx.Component:
    """Render an image from base64 or path."""
    if not img_src:
        return rx.fragment()

    if img_src.startswith("data:"):
        return rx.image(src=img_src, width="100%", max_width="600px", radius="medium")
    elif img_src.startswith("http://") or img_src.startswith("https://"):
        return rx.image(src=img_src, width="100%", max_width="600px", radius="medium")
    else:
        # Local file path - try to serve from assets
        return rx.image(
            src=f"/assets/{img_src}",
            width="100%",
            max_width="600px",
            radius="medium",
        )


def _question_area() -> rx.Component:
    """Render the question display area."""
    return rx.fragment(
        rx.cond(
            _get_bank_name() != "",
            rx.flex(
                # Question number
                rx.badge(
                    rx.text(
                        f"第 {_get_question().get('id', WorkspaceState.current_index + 1)} 题",
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
                    f"{WorkspaceState.current_index + 1} / {_get_total()}",
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
    q = _get_question()
    return rx.fragment(
        rx.cond(
            q.get("question"),
            rx.text(
                q["question"],
                size="5",
                weight="medium",
                color="var(--gray-12)",
                line_height="1.6",
                padding_y="4",
            ),
        ),
        # Render question images
        rx.foreach(
            q.get("images", []),
            lambda img: _render_image(img),
        ),
    )


def _options_area() -> rx.Component:
    """Render answer options."""
    q = _get_question()
    options = q.get("options", [])
    correct_answer = q.get("answer", "").strip().upper()

    def _option_item(option_text: str, index: int) -> rx.Component:
        """Single option component."""
        option_letter = chr(65 + index)  # A, B, C, D...
        is_selected = WorkspaceState.selected_option == index
        is_correct = option_letter == correct_answer

        # Determine background color based on state
        def get_bg():
            if WorkspaceState.is_painting:
                return "transparent"
            return rx.cond(
                is_selected & rx.state.is_true(WorkspaceState.show_explanation),
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
                is_selected & rx.state.is_true(WorkspaceState.show_explanation),
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
                    is_selected & rx.state.is_true(WorkspaceState.show_explanation),
                    rx.icon(
                        "check-circle" if is_correct else "x-circle",
                        size=20,
                        color="var(--green-8)" if is_correct else "var(--red-8)",
                    ),
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            width="100%",
            size="4",
            variant="surface",
            bg=get_bg(),
            border=get_border(),
            align_self="stretch",
            cursor="pointer" if not WorkspaceState.is_painting else "default",
            disabled=WorkspaceState.is_painting,
            on_click=WorkspaceState.select_option(index) if not WorkspaceState.is_painting else None,
            _hover=rx.cond(
                WorkspaceState.is_painting,
                {},
                {"bg": "var(--gray-3)"},
            ),
        )

    return rx.fragment(
        rx.cond(
            len(options) > 0,
            rx.flex(
                rx.foreach(options, _option_item),
                direction="vertical",
                spacing="3",
                width="100%",
            ),
        ),
    )


def _explanation_area() -> rx.Component:
    """Render answer explanation."""
    q = _get_question()
    return rx.fragment(
        rx.cond(
            WorkspaceState.show_explanation & q.get("explanation"),
            rx.card(
                rx.flex(
                    rx.text("答案解析", size="4", weight="bold", color="var(--gray-12)"),
                    rx.divider(),
                    rx.text(
                        q["explanation"],
                        size="3",
                        color="var(--gray-11)",
                        line_height="1.6",
                    ),
                    rx.foreach(
                        q.get("images", []),
                        lambda img: _render_image(img),
                    ),
                    direction="vertical",
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
    stats = WorkspaceState.get_answer_statistics()
    return rx.fragment(
        rx.cond(
            _get_bank_name() != "" & stats["total"] > 0,
            rx.flex(
                # Statistics display
                rx.card(
                    rx.flex(
                        rx.badge(
                            rx.text(f"答题：{stats['correct']}/{stats['total']}", size="3", weight="bold"),
                            color_scheme="green" if stats["accuracy"] >= "70%" else "yellow",
                            variant="solid",
                        ),
                        rx.text(
                            f"正确率：{stats['accuracy']}",
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
                        disabled=WorkspaceState.current_index >= _get_total() - 1,
                    ),
                    spacing="4",
                    width="100%",
                    justify="center",
                ),
                direction="vertical",
                spacing="2",
            ),
            rx.fragment(),
        ),
    )


def _toolbar() -> rx.Component:
    """Render the toolbar with navigation and painting controls."""
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
            _get_bank_name(),
            size="3",
            weight="medium",
            color="var(--gray-11)",
        ),

        rx.spacer(),

        # Painting toggle
        rx.button(
            rx.icon("pencil" if not WorkspaceState.is_painting else "pencil-off", size=20),
            size="3",
            variant="soft",
            color_scheme="orange" if WorkspaceState.is_painting else "gray",
            on_click=WorkspaceState.toggle_painting,
            tooltip="画板模式" if not WorkspaceState.is_painting else "退出画板",
            tooltip_shade="3",
        ),

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


def _painting_toolbar() -> rx.Component:
    """Render painting mode toolbar."""
    return rx.cond(
        WorkspaceState.is_painting,
        rx.flex(
            rx.button(
                rx.icon("pen-line", size=20),
                size="2",
                variant="soft",
                bg=rx.cond(
                    rx.state.is_true(WorkspaceState.eraser_mode),
                    "transparent",
                    rx.color("orange", "4"),
                ),
                on_click=WorkspaceState.toggle_eraser,
            ),
            rx.color_picker(
                rx.color_pickerTrigger(rx.icon("palette", size=18)),
                rx.color_pickerPortal(
                    rx.color_pickerContent(
                        rx.color_pickerThumb(rx.color_pickerColorSwatch(color="black")),
                        rx.color_pickerColorSwatch(color="#000000"),
                        rx.color_pickerColorSwatch(color="#ffffff"),
                        rx.color_pickerColorSwatch(color="#ef4444"),
                        rx.color_pickerColorSwatch(color="#22c55e"),
                        rx.color_pickerColorSwatch(color="#3b82f6"),
                        rx.color_pickerColorSwatch(color="#f59e0b"),
                        rx.color_pickerColorSwatch(color="#8b5cf6"),
                    ),
                ),
                on_change=WorkspaceState.set_pen_color,
            ),
            rx.slider(
                default_value=3,
                min=1,
                max=20,
                on_value_commit=WorkspaceState.set_pen_size,
                size="2",
                width="100px",
            ),
            rx.text(
                f"{WorkspaceState.pen_size}px",
                size="2",
                color="var(--gray-9)",
            ),
            rx.button(
                rx.icon("trash-2", size=18),
                size="2",
                variant="soft",
                color_scheme="red",
                on_click=WorkspaceState.clear_canvas,
                tooltip="清空画布",
            ),
            rx.button(
                rx.icon("download", size=18),
                size="2",
                variant="soft",
                color_scheme="green",
                on_click=rx.call_script(f"""
                    const canvas = document.getElementById('quiz-canvas');
                    if (canvas) {{
                        const dataURL = canvas.toDataURL('image/png');
                        const link = document.createElement('a');
                        link.download = 'quiz_screenshot.png';
                        link.href = dataURL;
                        link.click();
                    }}
                """),
                tooltip="截屏下载",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("x", size=20),
                "退出画板",
                size="3",
                color_scheme="red",
                variant="solid",
                on_click=WorkspaceState.toggle_painting,
            ),
            spacing="3",
        ),
    )


def _canvas_area() -> rx.Component:
    """Render the drawing canvas overlay."""
    return rx.fragment(
        rx.cond(
            WorkspaceState.is_painting,
            rx.html(
                rx.html.script(_get_canvas_script()),
                rx.html.canvas(
                    id="quiz-canvas",
                    style={
                        "position": "fixed",
                        "top": "0",
                        "left": "0",
                        "width": "100vw",
                        "height": "100vh",
                        "zIndex": "9999",
                        "cursor": rx.cond(
                            WorkspaceState.eraser_mode,
                            "grab",
                            "crosshair",
                        ),
                        "display": "block",
                    },
                ),
            ),
        ),
    )


def _get_canvas_script() -> str:
    """Generate canvas JavaScript without f-strings."""
    eraser_val = "true" if WorkspaceState.eraser_mode else "false"
    return """
    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    let penColor = '%s';
    let penSize = %d;
    let isEraser = %s;

    function initCanvas() {
        const canvas = document.getElementById('quiz-canvas');
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;

        const ctx = canvas.getContext('2d');
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        // Restore saved data
        var savedData = '%s';
        if (savedData) {
            var img = new Image();
            img.onload = function() { ctx.drawImage(img, 0, 0); };
            img.src = savedData;
        }

        canvas.addEventListener('mousedown', function(e) {
            isDrawing = true;
            lastX = e.offsetX;
            lastY = e.offsetY;
        });

        canvas.addEventListener('mousemove', function(e) {
            if (!isDrawing) return;
            ctx.strokeStyle = penColor;
            ctx.lineWidth = penSize;
            ctx.globalCompositeOperation = isEraser ? 'destination-out' : 'source-over';

            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(e.offsetX, e.offsetY);
            ctx.stroke();

            lastX = e.offsetX;
            lastY = e.offsetY;
        });

        canvas.addEventListener('mouseup', function() {
            isDrawing = false;
        });

        canvas.addEventListener('mouseleave', function() {
            isDrawing = false;
        });

        // Touch support
        canvas.addEventListener('touchstart', function(e) {
            e.preventDefault();
            var touch = e.touches[0];
            var rect = canvas.getBoundingClientRect();
            isDrawing = true;
            lastX = touch.clientX - rect.left;
            lastY = touch.clientY - rect.top;
        });

        canvas.addEventListener('touchmove', function(e) {
            e.preventDefault();
            if (!isDrawing) return;
            var touch = e.touches[0];
            var rect = canvas.getBoundingClientRect();
            ctx.strokeStyle = penColor;
            ctx.lineWidth = penSize;
            ctx.globalCompositeOperation = isEraser ? 'destination-out' : 'source-over';

            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(touch.clientX - rect.left, touch.clientY - rect.top);
            ctx.stroke();

            lastX = touch.clientX - rect.left;
            lastY = touch.clientY - rect.top;
        });

        canvas.addEventListener('touchend', function() {
            isDrawing = false;
        });
    }

    // Wait for Reflex to render
    window.addEventListener('reflex:loaded', initCanvas);
    if (document.readyState !== 'loading') initCanvas();
    """ % (
        WorkspaceState.pen_color,
        WorkspaceState.pen_size,
        eraser_val,
        WorkspaceState.canvas_data.replace("'", "\\'"),
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
            direction="vertical",
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
    return rx.fragment(
        rx.container(
            rx.flex(
                rx.flex(
                    _toolbar(),
                    _painting_toolbar(),
                    direction="vertical",
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
                                direction="vertical",
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
                direction="vertical",
                spacing="4",
                width="100%",
                height="100vh",
            ),
            style={
                "padding": "0",
                "max_width": "100vw",
                "height": "100vh",
            },
        ),
        _canvas_area(),
    )
