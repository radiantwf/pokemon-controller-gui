from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QGridLayout, QDialogButtonBox, QHBoxLayout, QComboBox

from PySide6.QtWidgets import QSpacerItem, QSizePolicy

class LaunchMacroParasDialog(QDialog):
    def __init__(self, parent, macro):
        super().__init__(parent)
        self.setWindowTitle('执行脚本')
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        row = self._add_title_label(0)
        row = self._add_row_spacer(row,20)
        row = self._add_script_paras(row, macro)
        row = self._add_row_spacer(row)
        row = self._add_buttons(row)
        self.adjustSize()

    def _add_title_label(self, row) -> int:
        title_label = QLabel('参数设置')
        font = QFont()
        font.setPointSize(18)
        title_label.setFont(font)
        self.layout.addWidget(title_label, row, 0, 1, 3)
        row += 1
        return row

    def _add_script_paras(self, row, macro) -> int:
        para_label = QLabel(f'循环次数')
        para_edit = QLineEdit(str(macro['loop']))
        self.layout.addWidget(para_label, row, 0, 1, 2)
        self.layout.addWidget(para_edit, row, 2, 1, 2)
        row += 1
        for para in macro['paras']:
            para_name = para['name']
            para_summary = para['summary']
            para_default = para['default']
            para_label = QLabel(f'{para_summary}')
            para_edit = QLineEdit(para_default)
            self.layout.addWidget(para_label, row, 0, 1, 2)
            self.layout.addWidget(para_edit, row, 2, 1, 2)
            row += 1
        return row
        

    def _add_row_spacer(self, row, height = 40) -> int:
        spacer = QSpacerItem(1, height, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer, row, 0)
        row += 1
        return row

    def _add_buttons(self, row) -> int:
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box, row, 2,1,2)
        row += 1
        return row
