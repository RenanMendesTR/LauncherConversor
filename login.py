from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation
import hashlib, requests

class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Conversor Domínio")
        self.setFixedSize(420, 240)

        # Frameless + transparência (mesmo estilo do launcher)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Container visual
        self.container = QLabel(self)
        self.container.setObjectName("main_widget")
        self.container.setGeometry(0, 0, 420, 240)

        # Campos
        self.label_title = QLabel("Entrar no SGD")
        self.label_title.setStyleSheet("font-family: Calibri; color: white; font-size: 18px;")
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário")
        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Senha")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)

        # Botões
        self.btn_login = QPushButton("Entrar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_login.setDefault(True)

        # Layouts
        form_layout = QVBoxLayout()
        form_layout.addWidget(self.label_title)
        form_layout.addSpacing(8)
        form_layout.addWidget(self.input_user)
        form_layout.addWidget(self.input_pass)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_login)
        form_layout.addLayout(btn_layout)

        wrapper = QVBoxLayout(self.container)
        wrapper.setContentsMargins(18, 18, 18, 18)
        wrapper.addLayout(form_layout)

        # Estilo visual igual ao launcher
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
        """)

        # Conexões
        self.btn_login.clicked.connect(self.on_try_login)
        self.btn_cancel.clicked.connect(self.reject)
        self.input_pass.returnPressed.connect(self.on_try_login)

        # 🎬 Inicia fade ao abrir
        self.start_fade_in()

    # --- EFEITO DE FADE-IN ---
    def start_fade_in(self):
        """Aplica um efeito de fade-in na abertura da janela"""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(700)  # duração em ms
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    # --- LOGIN ---
    def on_try_login(self):
        user = self.input_user.text().strip()
        password = self.input_pass.text().strip()

        if not user or not password:
            QMessageBox.warning(self, "Erro", "Preencha usuário e senha.")
            return

        self.btn_login.setEnabled(False)
        self.btn_login.setText("Verificando...")

        try:
            if self.authenticate_sgd(user, password):
                QMessageBox.information(self, "Sucesso", "Login realizado com sucesso!")
                self.accept()
            else:
                QMessageBox.warning(self, "Falha", "Usuário ou senha inválidos.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha na autenticação:\n{e}")
        finally:
            self.btn_login.setEnabled(True)
            self.btn_login.setText("Entrar")

    def authenticate_sgd(self, user, password):
        """Autentica no SGD usando a API da Domínio"""
        password_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        api = (
            "https://app01.dominiosistemas.com.br/loginVerifyServlet"
            f"?ps_xml=%3C?xml%20version=%221.0%22%20encoding=%22windows-1252%22%20?%3E"
            f"%3CverifyLogin%3E%3Clogin%3E{user}%3C/login%3E"
            f"%3Csenha%3E{password_md5}%3C/senha%3E"
            "%3Crestricao%3E1%3C/restricao%3E%3C/verifyLogin%3E"
        )
        response = requests.get(api, verify=False, timeout=15)
        return "<codigo_retorno>1</codigo_retorno>" in response.text
