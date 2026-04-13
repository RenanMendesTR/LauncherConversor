import hashlib, requests, ctypes, ctypes.wintypes, winreg
from PyQt6.QtWidgets import QMessageBox
from login_ui import LoginUI

_REG_KEY = r"Software\ConversorThomsonReuters\Launcher"


# --- Criptografia via Windows DPAPI (sem dependências externas) ---

class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi_encrypt(plaintext: str):
    data = plaintext.encode("utf-8")
    buf = ctypes.create_string_buffer(data)
    blob_in = _Blob(len(data), buf)
    blob_out = _Blob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    )
    if ok:
        result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result
    return None


def _dpapi_decrypt(ciphertext: bytes):
    buf = ctypes.create_string_buffer(ciphertext)
    blob_in = _Blob(len(ciphertext), buf)
    blob_out = _Blob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    )
    if ok:
        result = ctypes.string_at(blob_out.pbData, blob_out.cbData).decode("utf-8")
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result
    return None


# --- Operações no Registro do Windows ---

def _save_credentials(user: str, password: str):
    encrypted = _dpapi_encrypt(password)
    if encrypted is None:
        return
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_KEY) as key:
        winreg.SetValueEx(key, "remember", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "user", 0, winreg.REG_SZ, user)
        winreg.SetValueEx(key, "pass", 0, winreg.REG_BINARY, encrypted)


def _clear_credentials():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY,
                            access=winreg.KEY_WRITE) as key:
            for name in ("user", "pass"):
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
            winreg.SetValueEx(key, "remember", 0, winreg.REG_DWORD, 0)
    except (FileNotFoundError, OSError):
        pass


def _load_credentials():
    """Retorna (user, password, remember) do registro, ou ('', '', False)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY) as key:
            remember = winreg.QueryValueEx(key, "remember")[0] == 1
            if not remember:
                return "", "", False
            user = winreg.QueryValueEx(key, "user")[0]
            enc = bytes(winreg.QueryValueEx(key, "pass")[0])
            password = _dpapi_decrypt(enc) or ""
            return user, password, True
    except (FileNotFoundError, OSError):
        return "", "", False


# --- Janela de Login ---

class LoginWindow(LoginUI):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.btn_login.clicked.connect(self.on_try_login)
        self.btn_cancel.clicked.connect(self.reject)
        self.input_pass.returnPressed.connect(self.on_try_login)

        user, password, remember = _load_credentials()
        if remember:
            self.input_user.setText(user)
            self.input_pass.setText(password)
            self.check_remember.setChecked(True)

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
                if self.check_remember.isChecked():
                    _save_credentials(user, password)
                else:
                    _clear_credentials()
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
