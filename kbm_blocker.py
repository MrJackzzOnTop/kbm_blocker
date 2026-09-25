import sys
import platform
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject, QTimer, QUrl
from PyQt6.QtGui import QFont, QPixmap, QColor, QCursor, QDesktopServices

class Signals(QObject):
    toggle_keyboard = pyqtSignal()
    toggle_mouse = pyqtSignal()
    update_status = pyqtSignal(str)

class KBMBlocker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.os = platform.system()
        self.keyboard_blocked = False
        self.mouse_blocked = False
        self.key_sequence = []
        self.keyboard_hook = None
        self.blocking_hook = None
        self.hotkey_handles = []
        
        self.signals = Signals()
        self.signals.toggle_keyboard.connect(self.toggle_keyboard_from_hotkey)
        self.signals.toggle_mouse.connect(self.toggle_mouse_from_hotkey)
        self.signals.update_status.connect(self.update_status_label)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 300)
        
        self.setup_ui()
        self.center_window()
        

        self.install_keyboard_hook()
    
    def setup_ui(self):
        container = QFrame()
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        

        title_bar = self.create_title_bar()
        main_layout.addWidget(title_bar)
        

        content = QWidget()
        content.setStyleSheet("background-color: #2d2d2d;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 8)
        content_layout.setSpacing(12)
        content.setStyleSheet("""
            background-color: #2d2d2d;
            border: none;
        """)
        

        header = QHBoxLayout()
        header.setSpacing(10)
        
        icon_label = QLabel()
        icon_label.setFixedSize(50, 50)
        icon_pixmap = QPixmap("src/icon.png")
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setText("⌨️")
            icon_label.setStyleSheet("color: white; font-size: 24px;")
        header.addWidget(icon_label)
        
        title = QLabel("Keyboard and Mouse Blocker")
        title.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 500;")
        title.setFont(QFont("Segoe UI", 14))
        header.addWidget(title)
        header.addStretch()
        
        content_layout.addLayout(header)
        content_layout.addSpacing(10)
        

        keyboard_row = QHBoxLayout()
        keyboard_row.setSpacing(15)
        
        kb_label = QLabel("Block keyboard")
        kb_label.setStyleSheet("color: #ffffff; font-size: 15px;")
        kb_label.setFont(QFont("Segoe UI", 11))
        keyboard_row.addWidget(kb_label)
        
        arrow1 = QLabel("→")
        arrow1.setStyleSheet("color: #ffffff; font-size: 15px;")
        keyboard_row.addWidget(arrow1)
        keyboard_row.addStretch()
        
        self.btn_keyboard = QPushButton("Click or press Ctrl + K")
        self.btn_keyboard.setFixedSize(200, 32)
        self.btn_keyboard.setCheckable(True)
        self.btn_keyboard.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_keyboard.setStyleSheet("""
            QPushButton {
                background-color: #0d0d0d;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
            QPushButton:checked {
                background-color: #1a472a;
                color: #4ade80;
            }
        """)
        self.btn_keyboard.toggled.connect(self.on_keyboard_toggled)
        keyboard_row.addWidget(self.btn_keyboard)
        
        content_layout.addLayout(keyboard_row)
        

        mouse_row = QHBoxLayout()
        mouse_row.setSpacing(15)
        
        mouse_label = QLabel("Block mouse    ")
        mouse_label.setStyleSheet("color: #ffffff; font-size: 15px;")
        mouse_label.setFont(QFont("Segoe UI", 11))
        mouse_row.addWidget(mouse_label)
        
        arrow2 = QLabel("→")
        arrow2.setStyleSheet("color: #ffffff; font-size: 15px;")
        mouse_row.addWidget(arrow2)
        mouse_row.addStretch()
        
        self.btn_mouse = QPushButton("Click or press Ctrl + M")
        self.btn_mouse.setFixedSize(200, 32)
        self.btn_mouse.setCheckable(True)
        self.btn_mouse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_mouse.setStyleSheet("""
            QPushButton {
                background-color: #0d0d0d;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
            QPushButton:checked {
                background-color: #1a472a;
                color: #4ade80;
            }
        """)
        self.btn_mouse.toggled.connect(self.on_mouse_toggled)
        mouse_row.addWidget(self.btn_mouse)
        
        content_layout.addLayout(mouse_row)
        

        self.status_label = QLabel("Ready - Click a button to block")
        self.status_label.setStyleSheet("color: #888888; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        content_layout.addStretch()
        
        main_layout.addWidget(content)


        github_bar = QFrame()
        github_bar.setFixedHeight(34)
        github_bar.setStyleSheet("""
            QFrame {
                background-color: #0d0d0d;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        github_layout = QHBoxLayout(github_bar)
        github_layout.setContentsMargins(0, 0, 0, 0)
        
        github_link = QPushButton("https://github.com/mrjackzzontop")
        github_link.setFlat(True)
        github_link.setStyleSheet("color: #888888; font-size: 15px;")
        github_link.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        github_layout.addWidget(github_link)
        github_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/mrjackzzontop")))
        main_layout.addWidget(github_bar)
        
        self.setCentralWidget(container)
    
    def create_title_bar(self):
        bar = QFrame()
        bar.setFixedHeight(38)
        bar.setStyleSheet("""
            QFrame {
                background-color: #0d0d0d;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)
        
        title = QLabel("KBM Blocker v1.2 by MrJackzzOnTop")
        title.setStyleSheet("color: #ffffff; font-size: 12px;")
        layout.addWidget(title)
        layout.addStretch()
        
        btn_min = QPushButton("−")
        btn_min.setFixedSize(26, 22)
        btn_min.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #555555; }
        """)
        btn_min.clicked.connect(self.showMinimized)
        layout.addWidget(btn_min)
        
        btn_close = QPushButton("×")
        btn_close.setFixedSize(26, 22)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #c42b1c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #e74c3c; }
        """)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        
        bar.mousePressEvent = self.title_mouse_press
        bar.mouseMoveEvent = self.title_mouse_move
        self.drag_pos = None
        return bar
    
    def title_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def title_mouse_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
    
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
    
    def update_status_label(self, text):
        self.status_label.setText(text)
    
    def install_keyboard_hook(self):
        """Register global toggle shortcuts."""
        import keyboard
        self.hotkey_handles = [
            keyboard.add_hotkey(
                "ctrl+k", self.signals.toggle_keyboard.emit, suppress=True
            ),
            keyboard.add_hotkey(
                "ctrl+m", self.signals.toggle_mouse.emit, suppress=True
            ),
        ]
        print("Ctrl+K and Ctrl+M shortcuts installed")

    def toggle_keyboard_from_hotkey(self):
        self.btn_keyboard.setChecked(not self.btn_keyboard.isChecked())

    def toggle_mouse_from_hotkey(self):
        self.btn_mouse.setChecked(not self.btn_mouse.isChecked())
    
    def on_keyboard_toggled(self, checked):
        if checked:
            self.block_keyboard()
        else:
            self.unblock_keyboard()
    
    def on_mouse_toggled(self, checked):
        if checked:
            self.block_mouse()
        else:
            self.unblock_mouse()
    
    def block_keyboard(self):
        """Enable keyboard blocking"""
        import keyboard
        self.keyboard_blocked = True
        if self.blocking_hook is None:
            self.blocking_hook = keyboard.hook(self.filter_blocked_key, suppress=True)
        self.btn_keyboard.setText("🔓 Press Ctrl + K to unblock")
        self.signals.update_status.emit("Keyboard BLOCKED - Ctrl+K to unblock")
        print("Keyboard blocking enabled")

    def filter_blocked_key(self, event):
        """Suppress keys while preserving Ctrl+K and Ctrl+M as escape shortcuts."""
        import keyboard

        key = event.name.lower()
        if key in ("ctrl", "left ctrl", "right ctrl", "ctrl_l", "ctrl_r"):
            return True
        if key in ("k", "m") and keyboard.is_pressed("ctrl"):
            return True
        return False
    
    def unblock_keyboard(self):
        """Disable keyboard blocking"""
        import keyboard
        self.keyboard_blocked = False
        if self.blocking_hook is not None:
            keyboard.unhook(self.blocking_hook)
            self.blocking_hook = None
        self.btn_keyboard.setChecked(False)
        self.btn_keyboard.setText("Click or press Ctrl + K")
        self.signals.update_status.emit("Keyboard unblocked")
        print("Keyboard blocking disabled")
    
    def do_unlock_keyboard(self):
        self.unblock_keyboard()
    
    def block_mouse(self):
        """Block mouse"""
        self.mouse_blocked = True
        self.btn_mouse.setText("🔓 Press Ctrl + M to unblock")
        self.signals.update_status.emit("Mouse BLOCKED - Ctrl+M to unblock")
        
        self.mouse_running = True
        
        def block_mouse_loop():
            import pyautogui
            pyautogui.FAILSAFE = False
            
            while self.mouse_running and self.mouse_blocked:
                pyautogui.moveTo(0, 0)
                time.sleep(0.05)
        
        self.mouse_thread = threading.Thread(target=block_mouse_loop, daemon=True)
        self.mouse_thread.start()
        print("Mouse blocked")
    
    def unblock_mouse(self):
        """Unblock mouse"""
        self.mouse_blocked = False
        self.mouse_running = False
        self.btn_mouse.setChecked(False)
        self.btn_mouse.setText("Click or press Ctrl + M")
        self.signals.update_status.emit("Mouse unblocked")
        print("Mouse unblocked")
    
    def do_unlock_mouse(self):
        self.unblock_mouse()
    
    def closeEvent(self, event):
        import keyboard
        if self.blocking_hook:
            keyboard.unhook(self.blocking_hook)
            self.blocking_hook = None
        for hotkey_handle in self.hotkey_handles:
            keyboard.remove_hotkey(hotkey_handle)
        self.hotkey_handles.clear()
        self.unblock_keyboard()
        self.unblock_mouse()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = KBMBlocker()
    window.show()
    sys.exit(app.exec())
