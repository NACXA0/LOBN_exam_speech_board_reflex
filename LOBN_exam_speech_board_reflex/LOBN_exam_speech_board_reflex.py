import reflex as rx

from LOBN_exam_speech_board_reflex.pages.wellcome import wellcome
from LOBN_exam_speech_board_reflex.pages.workspace import workspace
from LOBN_exam_speech_board_reflex.pages.admin import admin


app = rx.App()
app.add_page(wellcome, route='/', title='选择题库', description='')
app.add_page(workspace, route='/workspace', title='讲题主页', description='')
app.add_page(admin, route='/admin', title='后台', description='')
