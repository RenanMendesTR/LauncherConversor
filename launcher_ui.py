from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class LauncherUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicializador Thomson Reuters ETL")
        self.setFixedSize(480, 360)
        self._mouse_drag_pos = None

        # Frameless + transparência
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Container principal
        self.container = QWidget(self)
        self.container.setObjectName("main_widget")
        self.container.setGeometry(0, 0, 480, 360)
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(8, 8, 8, 8)

        # ---- Barra superior personalizada ----
        upper_bar = QHBoxLayout()
        upper_bar.setContentsMargins(12, 0, 12, 0)

        # Título
        title = QLabel("Inicializador Thomson Reuters ETL")
        title.setStyleSheet("font-family: Calibri; color: white; font-size: 18px;")
        upper_bar.addWidget(title)
        upper_bar.addStretch()

        # Botões minimizar e fechar
        self.btn_min = QPushButton("—")
        self.btn_close = QPushButton("✕")

        self.btn_min.setFixedSize(32, 24)
        self.btn_min.setStyleSheet("""
            QPushButton {
                font-family: Calibri;
                color: white;
                background: transparent;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        self.btn_close.setFixedSize(32, 24)
        self.btn_close.setStyleSheet("""
            QPushButton {
                font-family: Calibri;
                color: white;
                background: transparent;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e81123;
            }
        """)
        upper_bar.addWidget(self.btn_min)
        upper_bar.addWidget(self.btn_close)

        # ---- Status e barra de progresso ----
        self.label_status = QLabel("Pronto")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setStyleSheet("font-family: Calibri; color: white; font-size: 16px;")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        # ---- Botões principais ----
        self.button_update = QPushButton("Verificar Atualizações")
        self.button_update.setStyleSheet("""
            QPushButton {
                font-family: Calibri;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 12px;
            }
        """)

        self.button_open = QPushButton("Abrir Aplicativo")
        self.button_open_active = """
            QPushButton {
                font-family: Calibri;
                background-color: #eb8125;
                color: white;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #f28e3c;
            }
        """
        self.button_open_inactive = """
            QPushButton {
                font-family: Calibri;
                background-color: #555555;
                color: #cccccc;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 12px;
            }
        """

        self.button_open.setEnabled(False)
        self.button_open.setStyleSheet(self.button_open_inactive)

        self.button_preset = QPushButton("Abrir Preset de Médias")
        self.button_preset.setEnabled(False)
        self.button_preset.setStyleSheet(self.button_open_inactive)

        # ---- Layout principal ----
        layout.addLayout(upper_bar)
        layout.addStretch()
        layout.addWidget(self.label_status)
        layout.addWidget(self.progress)
        layout.addStretch()
        layout.addWidget(self.button_update)
        layout.addWidget(self.button_open)
        layout.addWidget(self.button_preset)

        # ---- Estilo geral ----
        self.setStyleSheet("""
            QWidget#main_widget {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #030100, stop:1 #3d220c
                );
                border-radius: 12px;
            }
            QPushButton {
                font-family: Calibri;
                background-color: #eb8125;
                color: white;
                font-size: 14px;
                border-radius: 8px;
                padding: 8px 12px;
            }
            QPushButton:hover { background-color: #f28e3c; }
            QProgressBar {
                min-height: 18px;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background-color: #f28e3c;
            }
        """)

        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.container.setGraphicsEffect(shadow)

        # Fade-in na abertura
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(700)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.opacity_anim.start()

    # ---- Permite mover a janela ----
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._mouse_drag_pos:
            self.move(event.globalPosition().toPoint() - self._mouse_drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._mouse_drag_pos = None

    def set_open_button_active(self, active: bool):
        if active:
            self.button_open.setEnabled(True)
            self.button_open.setStyleSheet(self.button_open_active)
            self.button_preset.setEnabled(True)
            self.button_preset.setStyleSheet(self.button_open_active)
        else:
            self.button_open.setEnabled(False)
            self.button_open.setStyleSheet(self.button_open_inactive)
            self.button_preset.setEnabled(False)
            self.button_preset.setStyleSheet(self.button_open_inactive)
