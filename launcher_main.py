import sys, os, ftplib, zipfile, subprocess, io, json
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from launcher_ui import LauncherUI
from pathlib import Path
from login_main import LoginWindow
from PyQt6.QtWidgets import QDialog

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).resolve().parent

# Corrige caminhos relativos
LOCAL_APP_FOLDER = BASE_DIR / "Conversor"
LOCAL_VERSION_FILE = LOCAL_APP_FOLDER / "version.txt"

# Configurações do servidor FTP
FTP_HOST = 'ftp.dominiosistemas.com.br'
FTP_USER = 'supuns'
FTP_PASSWORD = '219a3bcb'
FTP_ROOT_PATH = '/unidades/Pub/Conversores/[Conversor Thomson Reuters]/Test_Launcher'


class LauncherApp(LauncherUI):
    def __init__(self):

        super().__init__()

        self.btn_close.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.button_update.clicked.connect(self.check_updates)
        self.button_open.clicked.connect(self.open_app)
        self.button_preset.clicked.connect(self.open_preset)
        self.local_version = self.read_local_version()
        self.set_open_button_active(False)

    def read_local_version(self):
        if LOCAL_VERSION_FILE.exists():
            return LOCAL_VERSION_FILE.read_text(encoding="utf-8").strip()
        return None

    def check_updates(self):
        try:
            self.label_status.setText("Conectando ao servidor FTP...")
            QApplication.processEvents()

            with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD, timeout=20) as ftp:
                ftp.cwd(FTP_ROOT_PATH)
                self.label_status.setText("Verificando versão no servidor...")
                QApplication.processEvents()

                version_data = io.BytesIO()
                ftp.retrbinary("RETR version.json", version_data.write)
                version_data.seek(0)
                data = json.load(version_data)

                remote_ver = data.get("version")
                remote_file = data.get("file_name")

                local_ver = self.read_local_version()
                if local_ver == remote_ver:
                    self.label_status.setText(f"Aplicativo já está atualizado! Versão {remote_ver}")
                    self.progress.setValue(100)
                    self.set_open_button_active(True)
                    return

                self.label_status.setText(f"Baixando versão {remote_ver}...")
                QApplication.processEvents()
                self.download_and_update(ftp, remote_file, remote_ver)

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao verificar atualizações:\n{e}")

    def download_and_update(self, ftp, file_name, version):
        try:
            path_zip = Path("update.zip")
            total_size = ftp.size(file_name)
            downloaded = 0

            self.label_status.setText("Baixando atualização...")
            self.progress.setValue(0)
            QApplication.processEvents()

            with open(path_zip, "wb") as f:
                def callback(data):
                    nonlocal downloaded
                    f.write(data)
                    downloaded += len(data)
                    progress_value = int(downloaded * 100 / total_size)
                    self.progress.setValue(progress_value)
                    QApplication.processEvents()

                ftp.retrbinary(f"RETR {file_name}", callback)

            self.label_status.setText("Extraindo arquivos...")
            self.progress.setValue(0)
            QApplication.processEvents()

            with zipfile.ZipFile(path_zip, "r") as zip_ref:
                members = zip_ref.infolist()
                total_files = len(members)
                extracted = 0

                for member in members:
                    zip_ref.extract(member, LOCAL_APP_FOLDER)
                    extracted += 1
                    progress_value = int(extracted * 100 / total_files)
                    self.progress.setValue(progress_value)
                    QApplication.processEvents()

            os.remove(path_zip)

            LOCAL_VERSION_FILE.write_text(version, encoding="utf-8")
            self.label_status.setText(f"Atualizado para {version}!")
            self.progress.setValue(100)
            self.set_open_button_active(True)
            QMessageBox.information(self, "Sucesso", f"Atualização concluída para {version}.")

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao atualizar:\n{e}")

    def open_app(self):
        app_path = LOCAL_APP_FOLDER / "start.exe"
        if not app_path.exists():
            QMessageBox.warning(self, "Erro", f"Arquivo não encontrado: {app_path}")
            return
        try:
            subprocess.Popen([str(app_path), "--auth", "THOMSON_KEY_2025"], cwd=LOCAL_APP_FOLDER)
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível iniciar o aplicativo:\n{e}")

    def open_preset(self):
        app_path = LOCAL_APP_FOLDER / "preset_medias.exe"
        if not app_path.exists():
            QMessageBox.warning(self, "Erro", f"Arquivo não encontrado: {app_path}")
            return
        try:
            subprocess.Popen([str(app_path), "--auth", "THOMSON_KEY_2025"], cwd=LOCAL_APP_FOLDER)
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível iniciar o preset:\n{e}")


def resource_path(relative_path):
    import sys, os
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon(resource_path("icone_multi.ico")))

    login_dialog = LoginWindow()
    result = login_dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        w = LauncherApp()
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)