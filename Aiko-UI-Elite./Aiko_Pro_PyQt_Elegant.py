import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QFrame, QFileDialog, QDialog, QComboBox,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPainterPath


# ──────────────────────────────────────────────
#  Helper: foto circular
# ──────────────────────────────────────────────
def make_circle_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
    """Recorta un QPixmap en forma circular."""
    scaled = pixmap.scaled(size, size,
                           Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return result


# ──────────────────────────────────────────────
#  Diálogo de Ajustes
# ──────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustes de Aiko")
        self.setFixedSize(420, 540)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 20px;
            }
            QLabel {
                color: #3C4043;
                font-size: 13px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 45, 40, 40)
        layout.setSpacing(16)

        # Título
        titulo = QLabel("Personalización")
        titulo.setFont(QFont("SF Pro Display", 22, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #202124; font-size: 22px;")
        layout.addWidget(titulo)

        btn_style = """
            QPushButton {
                background-color: #F8F9FA;
                border-radius: 14px;
                padding: 14px 18px;
                font-size: 14px;
                color: #202124;
                border: 1px solid #E0E0E0;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #F1F3F4;
                border: 1px solid #BDBDBD;
            }
            QPushButton:pressed {
                background-color: #E8EAED;
            }
        """

        # Fondo
        lbl_fondo = QLabel("🌌  Fondo de Pantalla")
        layout.addWidget(lbl_fondo)
        btn_fondo = QPushButton("  Elegir imagen...")
        btn_fondo.setStyleSheet(btn_style)
        btn_fondo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fondo.clicked.connect(parent.seleccionar_fondo)
        layout.addWidget(btn_fondo)

        # Foto de perfil
        lbl_foto = QLabel("👤  Foto de Perfil")
        layout.addWidget(lbl_foto)
        btn_foto = QPushButton("  Elegir foto...")
        btn_foto.setStyleSheet(btn_style)
        btn_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_foto.clicked.connect(parent.seleccionar_foto)
        layout.addWidget(btn_foto)

        # Color de acento
        lbl_color = QLabel("🎨  Color de Acento")
        layout.addWidget(lbl_color)
        self.combo = QComboBox()
        self.combo.addItems(["Azul", "Verde", "Morado", "Rosa", "Cyan", "Naranja"])
        self.combo.setCurrentText(parent.config.get("color", "Azul"))
        self.combo.setStyleSheet("""
            QComboBox {
                padding: 11px 14px;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                font-size: 14px;
                background: #F8F9FA;
                color: #202124;
            }
            QComboBox::drop-down { border: none; }
            QComboBox:hover { border: 1px solid #BDBDBD; }
        """)
        self.combo.currentTextChanged.connect(parent.cambiar_acento)
        layout.addWidget(self.combo)

        layout.addStretch()

        # Botón guardar
        color_btn = parent.accent_colors.get(parent.config.get("color", "Azul"), "#1A73E8")
        btn_cerrar = QPushButton("Guardar y Salir")
        btn_cerrar.setFixedHeight(52)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_btn};
                color: white;
                font-weight: bold;
                font-size: 15px;
                padding: 14px;
                border-radius: 16px;
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:pressed {{ background-color: {color_btn}CC; }}
        """)
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)


# ──────────────────────────────────────────────
#  Ventana Principal
# ──────────────────────────────────────────────
class AikoPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aiko Haruka  ·  Elite")
        self.resize(1280, 860)
        self.setMinimumSize(960, 640)

        self.config_file = Path("aiko_config.json")
        self.accent_colors = {
            "Azul":    "#1A73E8",
            "Verde":   "#34A853",
            "Morado":  "#8B46FF",
            "Rosa":    "#EA4C8C",
            "Cyan":    "#00B4D8",
            "Naranja": "#FB8C00",
        }
        self.config = self.cargar_config()

        # Fondo de pantalla (capa inferior)
        self.background_label = QLabel(self)
        self.background_label.setScaledContents(True)
        self.background_label.lower()
        self.background_label.hide()

        self.init_ui()
        self.aplicar_config_inicial()

    # ── Config ───────────────────────────────
    def cargar_config(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"fondo": "", "foto": "", "color": "Azul", "nombre": "Daniel"}

    def guardar_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    # ── UI ───────────────────────────────────
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_sidebar())
        main_layout.addWidget(self._build_chat_area(), stretch=1)

   # ── Sidebar CORREGIDO ────────────────────────
    def _build_sidebar(self) -> QFrame:
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(295)
        # 1. Usamos un ObjectName para que el estilo NO se herede en cascada
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: rgba(255, 255, 255, 0.95);
                border-right: 1px solid #E8EAED;
            }
        """)
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(24, 50, 24, 28)
        sb.setSpacing(0)

        # Logo
        self.logo = QLabel("Aiko")
        self.logo.setFont(QFont("SF Pro Display", 40, QFont.Weight.Bold))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 2. Forzamos transparencia total y quitamos márgenes residuales
        self.logo.setStyleSheet(
            "background: transparent; border: none; padding: 0px; margin: 0px;"
        )
        sb.addWidget(self.logo)

        sb.addSpacing(28)
        # ... (el resto del código del sidebar sigue igual)

    
        # Botón nuevo chat
        self.btn_new = QPushButton("＋  Nuevo chat")
        self.btn_new.setFixedHeight(52)
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.setFont(QFont("SF Pro Text", 14, QFont.Weight.Medium))
        self.btn_new.clicked.connect(self.nuevo_chat)
        sb.addWidget(self.btn_new)

        sb.addStretch()

        # Tarjeta de usuario
        self.user_card = QFrame()
        self.user_card.setFixedHeight(80)
        self.user_card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 20px;
                border: 1px solid #E8EAED;
            }
        """)
        user_lay = QHBoxLayout(self.user_card)
        user_lay.setContentsMargins(14, 0, 14, 0)
        user_lay.setSpacing(12)

        self.photo_label = QLabel()
        self.photo_label.setFixedSize(46, 46)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet("""
            border-radius: 23px;
            background: #F1F3F4;
            color: #9AA0A6;
            font-size: 22px;
        """)
        self.photo_label.setText("🙂")
        user_lay.addWidget(self.photo_label)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self.username = QLabel(self.config.get("nombre", "Daniel"))
        self.username.setFont(QFont("SF Pro Text", 14, QFont.Weight.Bold))
        self.username.setStyleSheet("border: none; background: transparent; color: #202124;")
        self.status_lbl = QLabel("En línea")
        self.status_lbl.setFont(QFont("SF Pro Text", 11))
        self.status_lbl.setStyleSheet("border: none; background: transparent; color: #34A853;")
        info_col.addWidget(self.username)
        info_col.addWidget(self.status_lbl)
        user_lay.addLayout(info_col)
        user_lay.addStretch()

        sb.addWidget(self.user_card)

        sb.addSpacing(10)

        # Botón configuración
        self.settings_btn = QPushButton("⚙  Configuración")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9AA0A6;
                font-size: 13px;
                border: none;
                padding: 6px;
            }
            QPushButton:hover { color: #5F6368; }
        """)
        self.settings_btn.clicked.connect(self.abrir_ajustes)
        sb.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return self.sidebar

    # ── Área de chat ─────────────────────────
    def _build_chat_area(self) -> QWidget:
        chat_container = QWidget()
        chat_container.setStyleSheet("background: transparent;")
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(60, 44, 60, 36)
        chat_layout.setSpacing(20)

        # Saludo
        self.greeting = QLabel(f"Hola, {self.config.get('nombre', 'Daniel')} 👋")
        self.greeting.setFont(QFont("SF Pro Display", 36, QFont.Weight.Bold))
        self.greeting.setStyleSheet("color: #202124;")
        chat_layout.addWidget(self.greeting)

        # Caja de mensajes
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.chat_box.setFont(QFont("SF Pro Text", 14))
        self.chat_box.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.90);
                border-radius: 25px;
                padding: 22px 26px;
                color: #202124;
                border: 1px solid #E8EAED;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #DADCE0;
                border-radius: 3px;
            }
        """)
        chat_layout.addWidget(self.chat_box, stretch=1)

        # Contenedor de entrada
        input_container = QFrame()
        input_container.setFixedHeight(72)
        input_container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 36px;
                border: 1px solid #E0E0E0;
            }
        """)
        input_lay = QHBoxLayout(input_container)
        input_lay.setContentsMargins(22, 0, 8, 0)
        input_lay.setSpacing(8)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Escribe a Aiko…")
        self.entry.setFont(QFont("SF Pro Text", 15))
        self.entry.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #202124;
            }
        """)
        self.entry.returnPressed.connect(self.enviar_mensaje)
        input_lay.addWidget(self.entry, stretch=1)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(56, 56)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFont(QFont("SF Pro Text", 20))
        self.send_btn.clicked.connect(self.enviar_mensaje)
        input_lay.addWidget(self.send_btn)

        chat_layout.addWidget(input_container)

        return chat_container

    # ── Mensajes ─────────────────────────────
    def enviar_mensaje(self):
        texto = self.entry.text().strip()
        if not texto:
            return
        self.chat_box.append(
            f'<p style="margin:6px 0;"><b style="color:#202124;">Tú:</b> {texto}</p>')
        self.entry.clear()
        QTimer.singleShot(
            480,
            lambda: self.chat_box.append(
                '<p style="margin:6px 0;"><b style="color:#1A73E8;">Aiko:</b> '
                '¡Recibido! ¿En qué más puedo ayudarte?</p>'
            )
        )

    def nuevo_chat(self):
        self.chat_box.clear()

    # ── Ajustes ──────────────────────────────
    def abrir_ajustes(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.aplicar_config_inicial()

    def seleccionar_fondo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir fondo", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp)")
        if ruta:
            self.config["fondo"] = ruta
            pix = QPixmap(ruta)
            self.background_label.setPixmap(pix)
            self.background_label.show()
            self.guardar_config()

    def seleccionar_foto(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir foto de perfil", "",
            "Imágenes (*.png *.jpg *.jpeg)")
        if ruta:
            self.config["foto"] = ruta
            pix = make_circle_pixmap(QPixmap(ruta), 46)
            self.photo_label.setPixmap(pix)
            self.photo_label.setText("")
            self.guardar_config()

    def cambiar_acento(self, nombre: str):
        self.config["color"] = nombre
        color = self.accent_colors.get(nombre, "#1A73E8")

        # Logo
        self.logo.setStyleSheet(f"color: {color};")

        # Botón nuevo chat
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }}
            QPushButton:hover {{ background-color: {color}DD; }}
            QPushButton:pressed {{ background-color: {color}BB; }}
        """)

        # Botón enviar
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 28px;
                font-size: 20px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {color}DD; }}
            QPushButton:pressed {{ background-color: {color}BB; }}
        """)

        self.guardar_config()

    def aplicar_config_inicial(self):
        color_nombre = self.config.get("color", "Azul")
        self.cambiar_acento(color_nombre)

        fondo = self.config.get("fondo", "")
        if fondo and Path(fondo).exists():
            self.background_label.setPixmap(QPixmap(fondo))
            self.background_label.show()

        foto = self.config.get("foto", "")
        if foto and Path(foto).exists():
            pix = make_circle_pixmap(QPixmap(foto), 46)
            self.photo_label.setPixmap(pix)
            self.photo_label.setText("")

        nombre = self.config.get("nombre", "Daniel")
        self.username.setText(nombre)
        self.greeting.setText(f"Hola, {nombre} 👋")

    # ── Resize ───────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.resize(self.size())


# ──────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # Base limpia multiplataforma
    window = AikoPro()
    window.show()
    sys.exit(app.exec())
