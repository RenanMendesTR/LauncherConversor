from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QHBoxLayout, QGraphicsDropShadowEffect, QComboBox
)
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, QPointF, pyqtSignal
import math


class GearButton(QWidget):
    """Botão de engrenagem desenhado com QPainter."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Parâmetros")
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._hovered:
            bg = QPainterPath()
            bg.addRoundedRect(QRectF(0, 0, 32, 24), 6, 6)
            p.fillPath(bg, QColor("#404040"))

        cx, cy = 16.0, 12.0
        outer_r = 8.0
        inner_r = 5.5
        hole_r = 3.0
        teeth = 8

        gear = QPainterPath()
        for i in range(teeth):
            a1 = math.radians(i * 360 / teeth - 360 / teeth / 4)
            a2 = math.radians(i * 360 / teeth + 360 / teeth / 4)
            a3 = math.radians((i + 0.5) * 360 / teeth - 360 / teeth / 4)
            a4 = math.radians((i + 0.5) * 360 / teeth + 360 / teeth / 4)

            if i == 0:
                gear.moveTo(cx + outer_r * math.cos(a1), cy + outer_r * math.sin(a1))
            else:
                gear.lineTo(cx + outer_r * math.cos(a1), cy + outer_r * math.sin(a1))
            gear.lineTo(cx + outer_r * math.cos(a2), cy + outer_r * math.sin(a2))
            gear.lineTo(cx + inner_r * math.cos(a3), cy + inner_r * math.sin(a3))
            gear.lineTo(cx + inner_r * math.cos(a4), cy + inner_r * math.sin(a4))
        gear.closeSubpath()

        hole = QPainterPath()
        hole.addEllipse(QPointF(cx, cy), hole_r, hole_r)
        gear = gear.subtracted(hole)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 210))
        p.drawPath(gear)
        p.end()


class LauncherUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicializador Thomson Reuters ETL")
        self.setFixedSize(480, 435)
        self._mouse_drag_pos = None

        # Frameless + transparência
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Container principal
        self.container = QWidget(self)
        self.container.setObjectName("main_widget")
        self.container.setGeometry(0, 0, 480, 435)
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(8, 8, 8, 8)

        # Barra superior personalizada
        upper_bar = QHBoxLayout()
        upper_bar.setContentsMargins(12, 0, 12, 0)

        # Título
        title = QLabel("Inicializador Thomson Reuters ETL")
        title.setStyleSheet("font-family: Calibri; color: white; font-size: 18px;")
        upper_bar.addWidget(title)
        upper_bar.addStretch()

        # Botões da barra superior
        _title_btn_style = """
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
        """

        self.btn_settings = GearButton()

        self.btn_min = QPushButton("—")
        self.btn_min.setFixedSize(32, 24)
        self.btn_min.setStyleSheet(_title_btn_style)

        self.btn_close = QPushButton("✕")
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

        upper_bar.addWidget(self.btn_settings)
        upper_bar.addWidget(self.btn_min)
        upper_bar.addWidget(self.btn_close)

        # Status e barra de progresso
        self.label_status = QLabel("Pronto")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setStyleSheet("font-family: Calibri; color: white; font-size: 16px;")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        _neon_orange = """
            QPushButton {
                font-family: Calibri;
                font-size: 18px;
                font-weight: bold;
                color: #1c0800;
                background-color: qradialgradient(
                    cx:0.5, cy:0.45, radius:0.85,
                    fx:0.5, fy:0.3,
                    stop:0   rgba(255, 200, 130, 255),
                    stop:0.4 rgba(235, 129,  37, 255),
                    stop:1   rgba(145,  68,   8, 255)
                );
                border-top:    1px solid rgba(255, 215, 155, 0.75);
                border-bottom: 1px solid rgba(130,  58,   8, 0.65);
                border-left:   1px solid rgba(245, 160,  75, 0.55);
                border-right:  1px solid rgba(245, 160,  75, 0.55);
                border-radius: 8px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: qradialgradient(
                    cx:0.5, cy:0.45, radius:0.85,
                    fx:0.5, fy:0.3,
                    stop:0   rgba(255, 215, 150, 255),
                    stop:0.4 rgba(245, 145,  55, 255),
                    stop:1   rgba(165,  82,  18, 255)
                );
                border-top: 1px solid rgba(255, 228, 175, 0.9);
            }
        """

        # Botões principais
        self.button_update = QPushButton("Verificar Atualizações")
        self.button_update.setFixedHeight(44)
        self.button_update.setStyleSheet(_neon_orange + """
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
                border: none;
            }
        """)

        self.button_open = QPushButton("Abrir Aplicativo")
        self.button_open.setFixedHeight(44)
        self.button_open_active = _neon_orange
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
        self.button_preset.setFixedHeight(44)
        self.button_preset.setEnabled(False)
        self.button_preset.setStyleSheet(self.button_open_inactive)

        # Painel de informação de versões
        self.version_panel = QWidget()
        self.version_panel.setObjectName("version_panel")
        version_vbox = QVBoxLayout(self.version_panel)
        version_vbox.setContentsMargins(12, 6, 12, 6)
        version_vbox.setSpacing(3)

        self.label_version_local = QLabel()
        self.label_version_local.setTextFormat(Qt.TextFormat.RichText)

        self.label_version_remote = QLabel()
        self.label_version_remote.setTextFormat(Qt.TextFormat.RichText)

        version_vbox.addWidget(self.label_version_local)
        version_vbox.addWidget(self.label_version_remote)

        self._set_version_display(self.label_version_local,  "Instalado: ", "—", "#555555")
        self._set_version_display(self.label_version_remote, "Disponível:", "—", "#555555")

        # Seletor de aplicativo
        combo_row = QHBoxLayout()
        combo_row.setContentsMargins(4, 0, 4, 0)

        lbl_app = QLabel("Aplicativo:")
        lbl_app.setStyleSheet("font-family: Calibri; font-size: 13px; color: #aaaaaa;")
        lbl_app.setFixedWidth(78)

        self.combo_app = QComboBox()
        self.combo_app.addItem("Conversor Thomson Reuters")
        self.combo_app.addItem("Conversor eSocial XML")
        self.combo_app.setFixedHeight(32)

        combo_row.addWidget(lbl_app)
        combo_row.addWidget(self.combo_app)

        # Layout principal
        layout.addLayout(upper_bar)
        layout.addSpacing(4)
        layout.addLayout(combo_row)
        layout.addStretch()
        layout.addWidget(self.label_status)
        layout.addWidget(self.progress)
        layout.addWidget(self.version_panel)
        layout.addStretch()
        layout.addWidget(self.button_update)
        layout.addWidget(self.button_open)
        layout.addWidget(self.button_preset)

        # Estilo geral
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
                color: #1c0800;
                font-weight: bold;
                font-size: 14px;
                background-color: qradialgradient(
                    cx:0.5, cy:0.45, radius:0.85,
                    fx:0.5, fy:0.3,
                    stop:0   rgba(255, 200, 130, 255),
                    stop:0.4 rgba(235, 129,  37, 255),
                    stop:1   rgba(145,  68,   8, 255)
                );
                border-top:    1px solid rgba(255, 215, 155, 0.75);
                border-bottom: 1px solid rgba(130,  58,   8, 0.65);
                border-left:   1px solid rgba(245, 160,  75, 0.55);
                border-right:  1px solid rgba(245, 160,  75, 0.55);
                border-radius: 8px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: qradialgradient(
                    cx:0.5, cy:0.45, radius:0.85,
                    fx:0.5, fy:0.3,
                    stop:0   rgba(255, 215, 150, 255),
                    stop:0.4 rgba(245, 145,  55, 255),
                    stop:1   rgba(165,  82,  18, 255)
                );
                border-top: 1px solid rgba(255, 228, 175, 0.9);
            }
            QProgressBar {
                min-height: 18px;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background-color: #f28e3c;
            }
            QWidget#version_panel {
                background: rgba(255,255,255,0.04);
                border-radius: 6px;
            }
            QComboBox {
                font-family: Calibri;
                font-size: 14px;
                color: white;
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(235, 129, 37, 0.45);
                border-radius: 6px;
                padding: 4px 10px;
            }
            QComboBox:hover {
                border: 1px solid rgba(235, 129, 37, 0.8);
                background-color: rgba(255, 255, 255, 0.11);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border-left: 1px solid rgba(235, 129, 37, 0.3);
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox QAbstractItemView {
                font-family: Calibri;
                font-size: 14px;
                background-color: #1e0d02;
                color: white;
                selection-background-color: #eb8125;
                selection-color: #1c0800;
                border: 1px solid rgba(235, 129, 37, 0.5);
                outline: none;
                padding: 2px;
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
        self.apply_messagebox_style()

    def apply_messagebox_style(self):
        self.setStyleSheet(self.styleSheet() + """
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
                font-family: Calibri;
                font-size: 14px;
            }
            QMessageBox QLabel {
                color: white;
                font-family: Calibri;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #eb8125;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QMessageBox QPushButton:hover {
                background-color: #f28e3c;
            }
        """)

    def _set_version_display(self, label, prefix: str, value: str, color: str):
        label.setText(
            f'<span style="font-family:Calibri;font-size:12px;color:#888888;">{prefix}</span>'
            f'&nbsp;&nbsp;<span style="font-family:Calibri;font-size:12px;font-weight:bold;color:{color};">{value}</span>'
        )

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
