import reflex as rx

config = rx.Config(
    app_name="LOBN_exam_speech_board_reflex",
    #frontend_port=3000,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)