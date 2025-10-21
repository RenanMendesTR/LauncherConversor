import sys, os, requests, zipfile, subprocess
from PyQt6.QtWidgets import QApplication, QMessageBox
from launcher_ui import LauncherUI
from pathlib import Path
from PyQt6.QtCore import QTimer

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).resolve().parent

# Corrige caminhos relativos
LOCAL_APP_FOLDER = BASE_DIR / "Conversor"
LOCAL_VERSION_FILE = LOCAL_APP_FOLDER / "version.txt"
SERVER_VERSION_URL = "http://localhost:8000/version.json"


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

        # QTimer.singleShot(800, self.check_updates)

    def read_local_version(self):
        if LOCAL_VERSION_FILE.exists():
            return LOCAL_VERSION_FILE.read_text(encoding="utf-8").strip()
        return None

    def check_updates(self):
        try:
            self.label_status.setText("Verificando atualizações...")
            self.progress.setValue(0)
            QApplication.processEvents()

            r = requests.get(SERVER_VERSION_URL, timeout=(5, 60))
            data = r.json()

            remote_ver = data.get("version")
            url = data.get("download_url")

            local_ver = self.read_local_version()
            if local_ver == remote_ver:
                self.label_status.setText(f"Aplicativo já está atualizado! Versão {remote_ver}")
                self.progress.setValue(100)
                self.set_open_button_active(True)
                return

            self.label_status.setText(f"Baixando versão {remote_ver}...")
            self.download_and_update(url, remote_ver)

        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def download_and_update(self, url, version):
        try:
            response = requests.get(url, stream=True, timeout=(5, 120))
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            path_zip = Path("update.zip")

            with open(path_zip, "wb") as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        self.progress.setValue(int(downloaded * 100 / total))

            with zipfile.ZipFile(path_zip, "r") as zip_ref:
                zip_ref.extractall(LOCAL_APP_FOLDER)
            os.remove(path_zip)

            LOCAL_VERSION_FILE.write_text(version, encoding="utf-8")
            self.label_status.setText(f"Atualizado para {version}!")
            self.progress.setValue(100)
            self.set_open_button_active(True)
            QMessageBox.information(self, "Sucesso", f"Atualização concluída para {version}.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = LauncherApp()
    w.show()
    sys.exit(app.exec())
