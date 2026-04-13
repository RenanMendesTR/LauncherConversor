from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QCheckBox, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation


class LoginUI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Conversor Domínio")
        self.setFixedSize(420, 265)

        # Frameless + transparência (igual ao launcher)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Container visual
        self.container = QLabel(self)
        self.container.setObjectName("main_widget")
        self.container.setGeometry(0, 0, 420, 265)

        # Campos
        self.label_title = QLabel("Entrar no SGD")
        self.label_title.setStyleSheet("font-family: Calibri; color: white; font-size: 18px;")
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário")
        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Senha")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)

        # Checkbox lembrar senha
        self.check_remember = QCheckBox("Lembrar senha")

        # Botões
        self.btn_login = QPushButton("Entrar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_login.setDefault(True)
        self.btn_login.setFixedSize(100, 34)
        self.btn_cancel.setFixedSize(100, 34)

        # Layouts
        form_layout = QVBoxLayout()
        form_layout.addWidget(self.label_title)
        form_layout.addSpacing(8)
        form_layout.addWidget(self.input_user)
        form_layout.addWidget(self.input_pass)
        form_layout.addWidget(self.check_remember)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_login)
        form_layout.addLayout(btn_layout)

        wrapper = QVBoxLayout(self.container)
        wrapper.setContentsMargins(18, 18, 18, 18)
        wrapper.addLayout(form_layout)

        self.setStyleSheet("""
            QWidget#main_widget {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #030100, stop:1 #3d220c
                );
                border-radius: 12px;
            }
            QLabel { color: white; font-family: Calibri; }
            QLineEdit {
                font-family: Calibri;
                font-size: 14px;
                padding: 8px;
                border-radius: 6px;
                background: rgba(255,255,255,0.06);
                color: white;
            }
            QPushButton {
                font-family: Calibri;
                background-color: #eb8125;
                color: white;
                font-size: 14px;
                border-radius: 8px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f28e3c; }
            QCheckBox {
                font-family: Calibri;
                font-size: 13px;
                color: #cccccc;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid #888888;
                background: rgba(255,255,255,0.06);
            }
            QCheckBox::indicator:checked {
                background-color: #eb8125;
                border: 1px solid #eb8125;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #f28e3c;
            }
        """)

        self.start_fade_in()

    def start_fade_in(self):
        """Aplica um efeito de fade-in na abertura da janela"""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(700)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
