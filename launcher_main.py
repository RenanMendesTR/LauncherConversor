import sys, os, ftplib, zipfile, subprocess, shutil, winreg
import requests
from PyQt6.QtWidgets import QApplication, QMessageBox, QMenu, QToolTip
from PyQt6.QtGui import QIcon, QCursor, QFontDatabase
from PyQt6.QtCore import Qt, QSettings
from launcher_ui import LauncherUI
from pathlib import Path
from login_main import LoginWindow
from PyQt6.QtWidgets import QDialog
from settings_ui import SettingsDialog, SETTINGS_ORG, SETTINGS_APP
from datetime import datetime

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).resolve().parent

# Credenciais FTP — valores de fallback caso o Gist não esteja acessível
_FTP_HOST_DEFAULT     = 'ftp.dominiosistemas.com.br'
_FTP_USER_DEFAULT     = 'supuns'
_FTP_PASSWORD_DEFAULT = 'VyML6iNOFsyttonm35VR40WuAcyr'

_FTP_CREDENTIALS_URL = (
    'https://gist.githubusercontent.com/RenanMendesTR/'
    '540cfe34c461ea73ba6c0f112fd7c910/raw/ftp_config.json'
)


def _load_ftp_credentials():
    """Busca credenciais FTP do Gist remoto; retorna fallback em caso de falha."""
    try:
        response = requests.get(_FTP_CREDENTIALS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data['host'], data['user'], data['password']
    except Exception:
        return _FTP_HOST_DEFAULT, _FTP_USER_DEFAULT, _FTP_PASSWORD_DEFAULT


FTP_HOST, FTP_USER, FTP_PASSWORD = _load_ftp_credentials()

# Caminho no Registro do Windows para armazenar os registros de atualização
_REG_PATH = r'SOFTWARE\DominioSistemas\LauncherConversor\Updates'


def _reg_read(value_name: str):
    """Lê um valor do Registro do Windows. Retorna None se não existir."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except OSError:
        return None


def _reg_write(value_name: str, value: str):
    """Grava um valor string no Registro do Windows, criando a chave se necessário."""
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _REG_PATH) as key:
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)


# Configurações por aplicativo (índice = posição no ComboBox)
APP_CONFIGS = {
    0: {
        "ftp_path":     "/unidades/Pub/Conversores/test_launcher/[Conversor Thomson Reuters]",
        "zip_name":     "Conversor-Thomson-Reuters.zip",
        "local_folder": BASE_DIR / "Conversor Thomson Reuters",
        "reg_key":      "ThomsonReuters",
        "start_exe":    "start.exe",
        "preset_exe":   "preset_medias.exe",
    },
    1: {
        "ftp_path":     "/unidades/Pub/Conversores/test_launcher/[Conversor eSocial]",
        "zip_name":     "conversorEsocial.zip",
        "local_folder": BASE_DIR / "Conversor eSocial XML",
        "reg_key":      "eSocial",
        "start_exe":    "main.exe",
        "preset_exe":   None,
    },
}


class LauncherApp(LauncherUI):
    def __init__(self):

        super().__init__()

        self.btn_close.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_settings.clicked.connect(self._open_settings)
        self.button_update.btn_main.clicked.connect(self._on_update_clicked)
        self.button_update.btn_arrow.clicked.connect(self._show_update_menu)
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
        """Retorna (mdtm, size) do Registro do Windows, ou None se não existir.
        Na primeira execução migra automaticamente qualquer .txt legado."""
        reg_key = self._cfg["reg_key"]
        raw = _reg_read(reg_key)

        # Migração: se ainda não existe no Registro, tenta importar do .txt legado
        if raw is None:
            legacy_names = {"ThomsonReuters": "last_update_thomson.txt",
                            "eSocial":        "last_update_esocial.txt"}
            legacy_file = BASE_DIR / legacy_names.get(reg_key, "")
            if legacy_file.exists():
                raw = legacy_file.read_text(encoding="utf-8").strip()
                _reg_write(reg_key, raw)
                try:
                    legacy_file.unlink()
                except OSError:
                    pass

        if raw:
            parts = raw.split("|")
            if len(parts) == 2:
                try:
                    return parts[0], int(parts[1])
                except ValueError:
                    pass
        return None

    def save_local_record(self, mdtm, size):
        _reg_write(self._cfg["reg_key"], f"{mdtm}|{size}")

    def get_remote_zip(self, ftp):
        """Retorna o nome do arquivo zip do aplicativo no servidor FTP."""
        target = self._cfg["zip_name"]
        files = ftp.nlst()
        if target not in files:
            raise RuntimeError(f"Arquivo '{target}' não encontrado no servidor.")
        return target

    def _format_mdtm(self, mdtm):
        """Converte string MDTM (YYYYMMDDHHmmss) UTC para horário local."""
        try:
            from datetime import timezone
            dt_utc = datetime.strptime(mdtm, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone()
            return dt_local.strftime("%d/%m/%Y %H:%M")
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

            host, user, password = _load_ftp_credentials()
            with ftplib.FTP(host, user, password, timeout=20) as ftp:
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

            host, user, password = _load_ftp_credentials()
            with ftplib.FTP(host, user, password, timeout=20) as ftp:
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

    def _build_launch_env(self) -> dict:
        """Monta o ambiente de execução herdado com as flags do Launcher."""
        env = os.environ.copy()
        env["CONV_AUTH"] = "THOMSON_KEY_2025"

        s = QSettings(SETTINGS_ORG, SETTINGS_APP)
        if s.value("settings/ignore_db_warning", False, type=bool):
            env["CONV_IGNORE_DB_WARNING"] = "1"
        else:
            env.pop("CONV_IGNORE_DB_WARNING", None)

        if s.value("settings/detect_unit", False, type=bool):
            env["CONV_DETECT_UNIT"] = "1"
        else:
            env.pop("CONV_DETECT_UNIT", None)

        if s.value("settings/client_code_conn", False, type=bool):
            env["CONV_CLIENT_CODE_CONN"] = "1"
        else:
            env.pop("CONV_CLIENT_CODE_CONN", None)

        return env

    def open_app(self):
        folder   = self._cfg["local_folder"]
        app_path = folder / self._cfg["start_exe"]
        if not app_path.exists():
            QMessageBox.warning(self, "Erro", f"Arquivo não encontrado: {app_path}")
            return
        try:
            subprocess.Popen([str(app_path)], cwd=folder, env=self._build_launch_env())
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
            subprocess.Popen([str(app_path)], cwd=folder, env=self._build_launch_env())
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível iniciar o preset:\n{e}")

    # ------------------------------------------------------------------
    # Dropdown do split button
    # ------------------------------------------------------------------

    def _show_update_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                font-family: Clario;
                font-size: 14px;
                background-color: #1e0d02;
                color: white;
                border: 1px solid rgba(235, 129, 37, 0.5);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #eb8125;
                color: #1c0800;
            }
        """)

        action_integrity = menu.addAction("Verificar Integridade")
        menu.addSeparator()
        action_uninstall = menu.addAction("Desinstalar")

        _tooltip_uninstall = (
            "⚠  Esta ação excluirá permanentemente todos os arquivos\n"
            "do aplicativo do disco. A operação não pode ser desfeita."
        )
        if action_uninstall is not None:
            action_uninstall.setToolTip(_tooltip_uninstall)
            action_uninstall.hovered.connect(
                lambda: QToolTip.showText(QCursor.pos(), _tooltip_uninstall)
            )

        btn_rect = self.button_update.btn_arrow.rect()
        global_pos = self.button_update.btn_arrow.mapToGlobal(btn_rect.bottomLeft())
        chosen = menu.exec(global_pos)

        if chosen == action_integrity:
            self._check_integrity()
        elif chosen == action_uninstall:
            self._uninstall_app()

    # ------------------------------------------------------------------
    # Verificação de integridade (local)
    # ------------------------------------------------------------------

    def _check_integrity(self):
        cfg = self._cfg
        folder   = cfg["local_folder"]
        exe_path = folder / cfg["start_exe"]

        folder_ok  = folder.exists()
        exe_ok     = exe_path.exists()
        record     = self.read_local_record()
        record_ok  = record is not None

        if folder_ok:
            total_files = sum(1 for _ in folder.rglob("*") if _.is_file())
        else:
            total_files = 0

        def mark(ok):
            return "✓" if ok else "✗"

        lines = [
            f"<b>Resultado da Verificação</b><br><br>",
            f"{mark(folder_ok)}  Pasta do aplicativo: "
            + (f"<span style='color:#6abf69;'>Encontrada</span>" if folder_ok
               else "<span style='color:#e05555;'>Não encontrada</span>"),
            f"<br>{mark(exe_ok)}  Executável principal (<i>{cfg['start_exe']}</i>): "
            + (f"<span style='color:#6abf69;'>Encontrado</span>" if exe_ok
               else "<span style='color:#e05555;'>Não encontrado</span>"),
            f"<br>{mark(record_ok)}  Registro de instalação: "
            + (f"<span style='color:#6abf69;'>Válido — {self._format_mdtm(record[0])}</span>" if record_ok
               else "<span style='color:#e05555;'>Ausente</span>"),
            f"<br>{'📁'}  Arquivos na pasta: <b>{total_files}</b>",
        ]

        msg = QMessageBox(self)
        msg.setWindowTitle("Verificação de Integridade")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("".join(lines))
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.exec()

    # ------------------------------------------------------------------
    # Desinstalação
    # ------------------------------------------------------------------

    def _uninstall_app(self):
        cfg    = self._cfg
        folder = cfg["local_folder"]
        app_name = self.combo_app.currentText()

        if not folder.exists():
            QMessageBox.information(self, "Desinstalar",
                                    "O aplicativo não está instalado.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar Desinstalação",
            f"Deseja desinstalar <b>{app_name}</b>?<br><br>"
            f"Todos os arquivos em:<br><i>{folder}</i><br><br>"
            f"serão excluídos permanentemente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            shutil.rmtree(folder)
            # Remove o registro de instalação do Registro do Windows
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH,
                                    access=winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, cfg["reg_key"])
            except OSError:
                pass

            self._load_app_state()
            self.progress.setValue(0)
            self.label_status.setText("Aplicativo desinstalado com sucesso.")
            QMessageBox.information(self, "Desinstalado",
                                    f"{app_name} foi removido com sucesso.")
        except Exception as e:
            QMessageBox.warning(self, "Erro ao Desinstalar",
                                f"Não foi possível remover os arquivos:\n{e}")


def resource_path(relative_path):
    import sys, os
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_bundled_fonts():
    """Registra as fontes Clario empacotadas com o aplicativo."""
    font_files = [
        "fonts/Clario-Regular.ttf",
        "fonts/Clario-Bold.ttf",
        "fonts/Clario-Medium.ttf",
        "fonts/Clario-Light.ttf",
    ]
    for font_file in font_files:
        path = resource_path(font_file)
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)


if __name__ == "__main__":
    # Evita o erro UpdateLayeredWindowIndirect em monitores com DPI scaling
    from PyQt6.QtCore import Qt as _Qt
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        _Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    load_bundled_fonts()

    app.setWindowIcon(QIcon(resource_path("icone_multi.ico")))

    login_dialog = LoginWindow()
    result = login_dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        w = LauncherApp()
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
