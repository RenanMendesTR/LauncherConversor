import sys, os, ftplib, zipfile, subprocess
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from launcher_ui import LauncherUI
from pathlib import Path
from login_main import LoginWindow
from PyQt6.QtWidgets import QDialog
from datetime import datetime

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).resolve().parent

LOCAL_APP_FOLDER = BASE_DIR / "Conversor"
LOCAL_UPDATE_RECORD = BASE_DIR / "last_update.txt"

# Configurações do servidor FTP
FTP_HOST = 'ftp.dominiosistemas.com.br'
FTP_USER = 'supuns'
FTP_PASSWORD = 'VyML6iNOFsyttonm35VR40WuAcyr'
FTP_ROOT_PATH = '/unidades/Pub/Conversores/[Conversor Thomson Reuters]'


class LauncherApp(LauncherUI):
    def __init__(self):

        super().__init__()

        self.btn_close.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.button_update.clicked.connect(self.check_updates)
        self.button_open.clicked.connect(self.open_app)
        self.button_preset.clicked.connect(self.open_preset)

        app_installed = (LOCAL_APP_FOLDER / "start.exe").exists()
        self.set_open_button_active(app_installed)

        record = self.read_local_record()
        self._local_mdtm = record[0] if record else None
        self._update_version_panel(self._local_mdtm, None)

        if self._local_mdtm:
            self.label_status.setText(f"Última atualização: {self._format_mdtm(self._local_mdtm)}")
        elif not app_installed:
            self.label_status.setText("Aplicativo não encontrado. Clique em Atualizar para instalar.")

    def read_local_record(self):
        """Retorna (mdtm, size) do registro local ou None se não existir."""
        if LOCAL_UPDATE_RECORD.exists():
            parts = LOCAL_UPDATE_RECORD.read_text(encoding="utf-8").strip().split("|")
            if len(parts) == 2:
                try:
                    return parts[0], int(parts[1])
                except ValueError:
                    pass
        return None

    def save_local_record(self, mdtm, size):
        LOCAL_UPDATE_RECORD.write_text(f"{mdtm}|{size}", encoding="utf-8")

    def get_remote_zip(self, ftp):
        """Lista o diretório FTP e retorna o nome do primeiro .zip encontrado."""
        files = ftp.nlst()
        zips = [f for f in files if f.lower().endswith(".zip")]
        if not zips:
            raise RuntimeError("Nenhum arquivo .zip encontrado no servidor.")
        return zips[0]

    def _format_mdtm(self, mdtm):
        """Converte string MDTM (YYYYMMDDHHmmss) para formato legível."""
        try:
            return datetime.strptime(mdtm, "%Y%m%d%H%M%S").strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return mdtm

    def _update_version_panel(self, local_mdtm, remote_mdtm):
        """Atualiza o painel de versões com código de cor."""
        local_date  = self._format_mdtm(local_mdtm)  if local_mdtm  else "—"
        remote_date = self._format_mdtm(remote_mdtm) if remote_mdtm else "—"

        if local_mdtm and remote_mdtm:
            if local_mdtm == remote_mdtm:
                local_color  = "#6abf69"   # verde: em dia
                remote_color = "#6abf69"
            else:
                local_color  = "#f0c040"   # amarelo: desatualizado
                remote_color = "#6abf69"   # verde: versão mais nova
        else:
            local_color  = "#eb8125" if local_mdtm  else "#555555"
            remote_color = "#eb8125" if remote_mdtm else "#555555"

        self._set_version_display(self.label_version_local,  "Instalado: ", local_date,  local_color)
        self._set_version_display(self.label_version_remote, "Disponível:", remote_date, remote_color)

    def check_updates(self):
        try:
            self.label_status.setText("Conectando ao servidor FTP...")
            self.button_update.setEnabled(False)
            QApplication.processEvents()

            with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD, timeout=20) as ftp:
                ftp.cwd(FTP_ROOT_PATH)
                self.label_status.setText("Verificando arquivos no servidor...")
                QApplication.processEvents()

                remote_file = self.get_remote_zip(ftp)
                ftp.voidcmd("TYPE I")  # modo binário obrigatório para SIZE e RETR
                remote_mdtm = ftp.sendcmd(f"MDTM {remote_file}").split()[1]
                remote_size = ftp.size(remote_file)

                self._update_version_panel(self._local_mdtm, remote_mdtm)
                QApplication.processEvents()

                local_record = self.read_local_record()
                if local_record:
                    local_mdtm, local_size = local_record
                    if remote_mdtm == local_mdtm and remote_size == local_size:
                        self.label_status.setText("Aplicativo já está atualizado!")
                        self.progress.setValue(100)
                        self.set_open_button_active(True)
                        self.set_update_button_default()
                        return

                self.label_status.setText("Nova versão detectada. Baixando...")
                QApplication.processEvents()
                self.download_and_update(ftp, remote_file, remote_mdtm, remote_size)

        except Exception as e:
            self.set_update_button_default()
            QMessageBox.warning(self, "Erro", f"Falha ao verificar atualizações:\n{e}")

    def set_update_button_default(self):
        self.button_update.setEnabled(True)
        self.button_update.setText("Verificar Atualizações")

    def download_and_update(self, ftp, file_name, remote_mdtm, remote_size):
        try:
            path_zip = BASE_DIR / "update.zip"
            downloaded = 0

            self.label_status.setText("Baixando atualização...")
            self.progress.setValue(0)
            QApplication.processEvents()

            with open(path_zip, "wb") as f:
                def callback(data):
                    nonlocal downloaded
                    f.write(data)
                    downloaded += len(data)
                    progress_value = int(downloaded * 100 / remote_size)
                    self.progress.setValue(progress_value)
                    QApplication.processEvents()

                ftp.retrbinary(f"RETR {file_name}", callback)

            self.label_status.setText("Extraindo arquivos...")
            self.progress.setValue(0)
            QApplication.processEvents()

            LOCAL_APP_FOLDER.mkdir(parents=True, exist_ok=True)
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

            path_zip.unlink()
            self.save_local_record(remote_mdtm, remote_size)
            self._local_mdtm = remote_mdtm
            self._update_version_panel(remote_mdtm, remote_mdtm)

            date_str = self._format_mdtm(remote_mdtm)
            self.label_status.setText(f"Última atualização: {date_str}")
            self.progress.setValue(100)
            self.set_open_button_active(True)
            self.set_update_button_default()
            QMessageBox.information(self, "Sucesso", f"Atualização concluída!\nModificado em: {date_str}")

        except Exception as e:
            self.set_update_button_default()
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