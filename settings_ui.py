from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, pyqtProperty, pyqtSignal


class ToggleSwitch(QWidget):
    """Botão deslizante estilo iOS/Android."""

    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._checked = checked
        self._circle_pos = 22.0 if checked else 4.0
        self._bg_color = QColor("#eb8125") if checked else QColor("#555555")

        self._anim = QPropertyAnimation(self, b"circle_pos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked
        self._animate()

    def _get_circle_pos(self):
        return self._circle_pos

    def _set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = pyqtProperty(float, _get_circle_pos, _set_circle_pos)

    def _animate(self):
        self._anim.stop()
        self._anim.setStartValue(self._circle_pos)
        self._anim.setEndValue(22.0 if self._checked else 4.0)
        self._bg_color = QColor("#eb8125") if self._checked else QColor("#555555")
        self._anim.start()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._animate()
        event.accept()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        t = (self._circle_pos - 4.0) / 18.0
        bg = QColor(
            int(0x55 + (0xeb - 0x55) * t),
            int(0x55 + (0x81 - 0x55) * t),
            int(0x55 + (0x25 - 0x55) * t),
        )

        track = QPainterPath()
        track.addRoundedRect(QRectF(0, 0, 48, 26), 13, 13)
        p.fillPath(track, bg)

        p.setBrush(QColor(255, 255, 255))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(self._circle_pos, 4.0, 18.0, 18.0))
        p.end()


def _make_option_row(text, checked=False):
    """Cria uma linha com label + toggle switch."""
    row = QHBoxLayout()
    row.setContentsMargins(12, 6, 12, 6)

    label = QLabel(text)
    label.setStyleSheet(
        "font-family: Clario; font-size: 14px; color: #dddddd; background: transparent;"
    )
    label.setWordWrap(True)

    toggle = ToggleSwitch(checked=checked)

    row.addWidget(label, 1)
    row.addWidget(toggle, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return row, toggle


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parâmetros")
        self.setFixedSize(420, 310)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._mouse_drag_pos = None

        container = QWidget(self)
        container.setObjectName("settings_container")
        container.setGeometry(0, 0, 420, 310)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        # -- Barra superior --
        header = QHBoxLayout()
        header.setContentsMargins(12, 4, 12, 4)

        title = QLabel("⚙  Parâmetros")
        title.setStyleSheet(
            "font-family: Clario; color: white; font-size: 17px; font-weight: bold; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        btn_close = QPushButton_X()
        btn_close.clicked.connect(self.close)
        header.addWidget(btn_close)

        main_layout.addLayout(header)
        main_layout.addSpacing(8)

        # -- Separador --
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(235, 129, 37, 0.3);")
        main_layout.addWidget(sep)
        main_layout.addSpacing(12)

        # -- Opções --
        row1, self.toggle_detect_unit = _make_option_row(
            "Detectar unidade automaticamente"
        )
        row2, self.toggle_ignore_db_warning = _make_option_row(
            "Ignorar aviso sobre banco de dados das inscrições"
        )
        row3, self.toggle_client_code_conn = _make_option_row(
            "Utilizar código do cliente como nome da conexão do Sybase"
        )

        main_layout.addLayout(row1)
        main_layout.addSpacing(4)
        self._add_separator(main_layout)
        main_layout.addSpacing(4)
        main_layout.addLayout(row2)
        main_layout.addSpacing(4)
        self._add_separator(main_layout)
        main_layout.addSpacing(4)
        main_layout.addLayout(row3)

        main_layout.addStretch()

        # -- Estilo geral --
        self.setStyleSheet("""
            QWidget#settings_container {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #030100, stop:1 #3d220c
                );
                border-radius: 12px;
                border: 1px solid rgba(235, 129, 37, 0.35);
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        container.setGraphicsEffect(shadow)

        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(350)
        self._fade_anim.setStartValue(0)
        self._fade_anim.setEndValue(1)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._fade_anim.start()

    @staticmethod
    def _add_separator(layout):
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.06);")
        layout.addWidget(sep)

    # -- Arrastar janela --
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


class QPushButton_X(QWidget):
    """Botão de fechar minimalista."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._hovered:
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, 28, 22), 6, 6)
            p.fillPath(path, QColor("#e81123"))

        p.setPen(QColor(255, 255, 255))
        cx, cy = 14, 11
        size = 4
        p.drawLine(int(cx - size), int(cy - size), int(cx + size), int(cy + size))
        p.drawLine(int(cx + size), int(cy - size), int(cx - size), int(cy + size))
        p.end()
