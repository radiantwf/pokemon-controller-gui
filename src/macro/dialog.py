from . import macro
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QDialogButtonBox, QHBoxLayout, QComboBox


class ScriptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        m = macro.Macro()
        self.script_json = m._publish
        self.setWindowTitle('运行本地脚本')
        self.layout = QGridLayout()
        self.layout.setRowMinimumHeight(50, 50)
        self.setLayout(self.layout)

        row = self._add_script_label(0)
        row = self._add_script_combobox(row)
        row = self._add_title_label(row)
        self._script_paras = -1
        row = self._add_script_paras(row)

    def _add_script_label(self, row) -> int:
        script_label = QLabel('脚本选择')
        font = QFont()
        font.setPointSize(26)
        script_label.setFont(font)
        self.layout.addWidget(script_label, row, 0, 1, 3)
        row += 1
        return row

    def _add_script_combobox(self, row) -> int:
        self.script_combobox = QComboBox()
        for script in self.script_json:
            script_summary = script['summary']
            self.script_combobox.addItem(script_summary)
        self.script_combobox.currentIndexChanged.connect(
            self._add_script_paras)
        self.layout.addWidget(self.script_combobox, row, 0, 1, 3)
        row += 1
        return row

    def _add_title_label(self, row) -> int:
        title_label = QLabel('参数选择')
        font = QFont()
        font.setPointSize(18)
        title_label.setFont(font)
        self.layout.addWidget(title_label, row, 0, 1, 3)
        row += 1
        return row

    def _add_script_paras(self, row) -> int:
        if self._script_paras < 0:
            self._script_paras = row
        row = self._script_paras
        for x in range(self.layout.rowCount()):
            if x < row:
                continue
            for y in range(self.layout.columnCount()):
                item = self.layout.itemAtPosition(x, y)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
        index = self.script_combobox.currentIndex()
        script = self.script_json[index]
        para_label = QLabel(f'循环次数')
        para_edit = QLineEdit(str(script['loop']))
        self.layout.addWidget(para_label, row, 0, 1, 2)
        self.layout.addWidget(para_edit, row, 2, 1, 1)
        row += 1
        for para in script['paras']:
            para_name = para['name']
            para_summary = para['summary']
            para_default = para['default']
            para_label = QLabel(f'{para_summary}')
            para_edit = QLineEdit(para_default)
            self.layout.addWidget(para_label, row, 0, 1, 2)
            self.layout.addWidget(para_edit, row, 2, 1, 2)
            row += 1
        
        row = self._add_buttons(row)
        self.adjustSize()

    def _add_buttons(self, row) -> int:
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box, row, 2,1,1)
        row += 1
        return row
