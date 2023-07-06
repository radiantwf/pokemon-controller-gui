
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

from . import macro

class ScriptDialog(QDialog):
    def __init__(self,parent = None):
        super().__init__(parent)
        m = macro.Macro()
        self.script_json = m._publish
        self.setWindowTitle('选择脚本')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self._add_script_widgets()

    def _add_script_widgets(self):
        for script in self.script_json:
            script_name = script['name']
            script_summary = script['summary']
            script_paras = script['paras']
            script_button = QPushButton(script_name)
            script_button.clicked.connect(lambda _, s=script: self._show_script_dialog(s))
            self.layout.addWidget(script_button)

    def _show_script_dialog(self, script):
        dialog = QDialog()
        dialog.setWindowTitle(script['name'])
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        for para in script['paras']:
            para_name = para['name']
            para_summary = para['summary']
            para_default = para['default']
            para_label = QLabel(f'{para_name}: {para_summary}')
            para_edit = QLineEdit(para_default)
            layout.addWidget(para_label)
            layout.addWidget(para_edit)
        ok_button = QPushButton('OK')
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)
        dialog.exec_()