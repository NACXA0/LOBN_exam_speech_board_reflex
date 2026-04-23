import reflex as rx

from LOBN_exam_speech_board_reflex.pages.workspace import workspace, WorkspaceState
from LOBN_exam_speech_board_reflex.pages.admin import admin, AdminState
from LOBN_exam_speech_board_reflex.pages.edit_questions import edit_questions, EditQuestionsState


app = rx.App()
app.add_page(admin, route='/', title='控制台', description='', on_load=AdminState.initialize)
app.add_page(workspace, route='/workspace', title='讲题主页', description='', on_load=WorkspaceState.load_whiteboard_settings)
app.add_page(edit_questions, route='/edit-questions/[bank]', title='编辑试题', on_load=EditQuestionsState.load_bank_from_url)

