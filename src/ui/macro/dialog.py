from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QGridLayout, QDialogButtonBox, QHBoxLayout, QComboBox
from PySide6.QtGui import QIntValidator, QDoubleValidator, QRegularExpressionValidator, QValidator, QFont
from PySide6.QtCore import QRegularExpression
from PySide6.QtWidgets import QSpacerItem, QSizePolicy

class LaunchMacroParasDialog(QDialog):
    def __init__(self, parent, macro):
        super().__init__(parent)
        self._macro = macro.copy()
        self._edit_widgets = dict()
        self._bool_validator = QRegularExpressionValidator(QRegularExpression('^(true|false)$', QRegularExpression.CaseInsensitiveOption))
        self._int_validator = QIntValidator()
        self._double_validator = QDoubleValidator()
        self.setWindowTitle('执行脚本')
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        row = self._add_title_label(0)
        row = self._add_row_spacer(row,20)
        row = self._add_script_paras(row)
        row = self._add_row_spacer(row,30)
        row = self._add_buttons(row)
        self.adjustSize()

    def get_macro_script(self)->dict:
        macro = self._macro.copy()
        macro['loop'] = int(self._edit_widgets['loop'].text())
        for para in macro['paras']:
            para['value'] = self._edit_widgets['paras'][para['name']].text()
        return macro


    def _add_title_label(self, row) -> int:
        title_label = QLabel('参数设置')
        font = QFont()
        font.setPointSize(18)
        title_label.setFont(font)
        self.layout.addWidget(title_label, row, 0, 1, 3)
        row += 1
        return row

    def _add_script_paras(self, row) -> int:
        para_label = QLabel(f'循环次数')
        para_edit = QLineEdit(str(self._macro['loop']))
        para_edit.setValidator(self._int_validator)
        self.layout.addWidget(para_label, row, 0, 1, 2)
        self.layout.addWidget(para_edit, row, 2, 1, 2)
        self._edit_widgets["loop"] = para_edit
        self._edit_widgets["paras"] = dict()
        row += 1
        for para in self._macro['paras']:
            para_name = para['name']
            para_summary = para['summary']
            para_default = para['default']
            para_label = QLabel(f'{para_summary}')
            para_edit = QLineEdit(para_default)
            self._set_lineEdit_validator(para_edit, para_default)
            self.layout.addWidget(para_label, row, 0, 1, 2)
            self.layout.addWidget(para_edit, row, 2, 1, 2)
            self._edit_widgets["paras"][para['name']] = para_edit
            row += 1
        return row
        
    def _set_lineEdit_validator(self,widget:QLineEdit, default_value:str):
        state,_,_ = self._bool_validator.validate(default_value, 0)
        if state == QValidator.Acceptable:
            widget.setValidator(self._bool_validator)
            return
        state,_,_ = self._int_validator.validate(default_value, 0)
        if state == QValidator.Acceptable:
            widget.setValidator(self._int_validator)
            return
        state,_,_ = self._double_validator.validate(default_value, 0)
        if state == QValidator.Acceptable:
            widget.setValidator(self._double_validator)
            return


    def _add_row_spacer(self, row, height = 10) -> int:
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
