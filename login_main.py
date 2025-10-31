import hashlib, requests
from PyQt6.QtWidgets import QMessageBox
from login_ui import LoginUI


class LoginWindow(LoginUI):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Conexões de botões
        self.btn_login.clicked.connect(self.on_try_login)
        self.btn_cancel.clicked.connect(self.reject)
        self.input_pass.returnPressed.connect(self.on_try_login)

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
