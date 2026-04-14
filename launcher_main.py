import sys, os, ftplib, zipfile, subprocess
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from launcher_ui import LauncherUI
from pathlib import Path
from login_main import LoginWindow
from PyQt6.QtWidgets import QDialog
from settings_ui import SettingsDialog
from settings_ui import SettingsDialog
from settings_ui import SettingsDialog
from datetime import datetime

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).resolve().parent

# Credenciais FTP
FTP_HOST     = 'ftp.dominiosistemas.com.br'
FTP_USER     = 'supuns'
FTP_PASSWORD = 'VyML6iNOFsyttonm35VR40WuAcyr'

# Configurações por aplicativo (índice = posição no ComboBox)
APP_CONFIGS = {
    0: {
        "ftp_path":      "/unidades/Pub/Conversores/[Conversor Thomson Reuters]",
        "zip_name":      "Conversor-Thomson-Reuters.zip",
        "local_folder":  BASE_DIR / "Conversor Thomson Reuters",
        "update_record": BASE_DIR / "last_update_thomson.txt",
        "start_exe":     "start.exe",
        "preset_exe":    "preset_medias.exe",
    },
    1: {
        "ftp_path":      "/unidades/Pub/Conversores/[Conversor eSocial]",
        "zip_name":      "conversorEsocial.zip",
        "local_folder":  BASE_DIR / "Conversor eSocial XML",
        "update_record": BASE_DIR / "last_update_esocial.txt",
        "start_exe":     "main.exe",
        "preset_exe":    None,
    },
}


class LauncherApp(LauncherUI):
    def __init__(self):

        super().__init__()

        self.btn_close.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_settings.clicked.connect(self._open_settings)
        self.button_update.clicked.connect(self._on_update_clicked)
        self.button_open.clicked.connect(self.open_app)
        self.button_preset.clicked.connect(self.open_preset)
        self.combo_app.currentIndexChanged.connect(self._on_app_changed)

        self._pending_remote_file = None
        self._pending_remote_mdtm = None
        self._pending_remote_size = None

        self._load_app_state()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def set_open_button_active(self, active: bool):
        if active:
            self.button_open.setEnabled(True)
            self.button_open.setStyleSheet(self.button_open_active)
        else:
            self.button_open.setEnabled(False)
            self.button_open.setStyleSheet(self.button_open_inactive)

        # Preset só é habilitado se o app suporta e está instalado
        preset_active = active and self._cfg["preset_exe"] is not None
        if preset_active:
            self.button_preset.setEnabled(True)
            self.button_preset.setStyleSheet(self.button_open_active)
        else:
            self.button_preset.setEnabled(False)
            self.button_preset.setStyleSheet(self.button_open_inactive)

    @property
    def _cfg(self):
        """Retorna a configuração do aplicativo atualmente selecionado."""
        return APP_CONFIGS[self.combo_app.currentIndex()]

    def _load_app_state(self):
        """Carrega o estado (versão instalada, botões) para o app selecionado."""
        app_installed = (self._cfg["local_folder"] / self._cfg["start_exe"]).exists()
        self.set_open_button_active(app_installed)

        record = self.read_local_record()
        self._local_mdtm = record[0] if record else None
        self._update_version_panel(self._local_mdtm, None)

        if self._local_mdtm:
            self.label_status.setText(f"Última atualização: {self._format_mdtm(self._local_mdtm)}")
        elif not app_installed:
            self.label_status.setText("Aplicativo não encontrado. Clique em Atualizar para instalar.")
        else:
            self.label_status.setText("Pronto")

    def _on_app_changed(self, index):
        self.set_update_button_default()
        self.progress.setValue(0)
        self._load_app_state()

    def read_local_record(self):
        """Retorna (mdtm, size) do registro local ou None se não existir."""
        record_file = self._cfg["update_record"]
        if record_file.exists():
            parts = record_file.read_text(encoding="utf-8").strip().split("|")
            if len(parts) == 2:
                try:
                    return parts[0], int(parts[1])
                except ValueError:
                    pass
        return None

    def save_local_record(self, mdtm, size):
        self._cfg["update_record"].write_text(f"{mdtm}|{size}", encoding="utf-8")

    def get_remote_zip(self, ftp):
        """Retorna o nome do arquivo zip do aplicativo no servidor FTP."""
        target = self._cfg["zip_name"]
        files = ftp.nlst()
        if target not in files:
            raise RuntimeError(f"Arquivo '{target}' não encontrado no servidor.")
        return target

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

    def _on_update_clicked(self):
        if self._pending_remote_file:
            self._start_download()
        else:
            self.check_updates()

    def check_updates(self):
        try:
            self.label_status.setText("Conectando ao servidor FTP...")
            self.button_update.setEnabled(False)
            QApplication.processEvents()

            with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD, timeout=20) as ftp:
                ftp.cwd(self._cfg["ftp_path"])
                self.label_status.setText("Verificando arquivos no servidor...")
                QApplication.processEvents()

                remote_file = self.get_remote_zip(ftp)
                ftp.voidcmd("TYPE I")
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

                # Nova versão detectada — aguarda confirmação do usuário
                self._pending_remote_file = remote_file
                self._pending_remote_mdtm = remote_mdtm
                self._pending_remote_size = remote_size
                self.label_status.setText(
                    f"Nova versão disponível: {self._format_mdtm(remote_mdtm)}"
                )
                self.button_update.setEnabled(True)
                self.button_update.setText("⬇  Atualizar")
                self.button_update.repaint()

        except Exception as e:
            self.set_update_button_default()
            QMessageBox.warning(self, "Erro", f"Falha ao verificar atualizações:\n{e}")

    def _start_download(self):
        try:
            self.button_update.setEnabled(False)
            self.label_status.setText("Conectando ao servidor FTP...")
            QApplication.processEvents()

            with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD, timeout=20) as ftp:
                ftp.cwd(self._cfg["ftp_path"])
                ftp.voidcmd("TYPE I")
                self.download_and_update(
                    ftp,
                    self._pending_remote_file,
                    self._pending_remote_mdtm,
                    self._pending_remote_size,
                )
        except Exception as e:
            self.set_update_button_default()
            QMessageBox.warning(self, "Erro", f"Falha ao iniciar atualização:\n{e}")

    def set_update_button_default(self):
        self._pending_remote_file = None
        self._pending_remote_mdtm = None
        self._pending_remote_size = None
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

            local_folder = self._cfg["local_folder"]
            local_folder.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(path_zip, "r") as zip_ref:
                members = zip_ref.infolist()
                total_files = len(members)
                extracted = 0

                for member in members:
                    zip_ref.extract(member, local_folder)
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
        folder   = self._cfg["local_folder"]
        app_path = folder / self._cfg["start_exe"]
        if not app_path.exists():
            QMessageBox.warning(self, "Erro", f"Arquivo não encontrado: {app_path}")
            return
        try:
            subprocess.Popen([str(app_path), "--auth", "THOMSON_KEY_2025"], cwd=folder)
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível iniciar o aplicativo:\n{e}")

    def open_preset(self):
        if not self._cfg["preset_exe"]:
            return
        folder   = self._cfg["local_folder"]
        app_path = folder / self._cfg["preset_exe"]
        if not app_path.exists():
            QMessageBox.warning(self, "Erro", f"Arquivo não encontrado: {app_path}")
            return
        try:
            subprocess.Popen([str(app_path), "--auth", "THOMSON_KEY_2025"], cwd=folder)
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível iniciar o preset:\n{e}")


def resource_path(relative_path):
    import sys, os
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


if __name__ == "__main__":
    # Evita o erro UpdateLayeredWindowIndirect em monitores com DPI scaling
    from PyQt6.QtCore import Qt as _Qt
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        _Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
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
