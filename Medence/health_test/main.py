import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout)
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QPainter
from PyQt5.QtCore import Qt, QRectF
os.environ["DISPLAY"] = ":0"  # 强制本地显示

class GradientFrame(QFrame):
    def __init__(self, color1, color2, parent=None):
        super().__init__(parent)
        self.color1 = QColor(color1)
        self.color2 = QColor(color2)
        self.setMinimumSize(180, 172)  # 调整为更合适的卡片尺寸

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.color1)
        gradient.setColorAt(1, self.color2)
        painter.fillRect(QRectF(0, 0, self.width(), self.height()), gradient)
        painter.end()


class HealthCheckApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能健康体检系统 - Linux版")
        self.setGeometry(75, 55, 930, 180)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                font-family: 'Noto Sans CJK SC';
            }
            QPushButton {
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        # Linux环境下程序映射
        self.program_map = {
            "血氧检测": (os.path.join("scripts", "oil.py"), "py"),
            "视力检测": (os.path.join("bin", "EyesTest"), "exe"),
            "身高测量": (os.path.join("scripts", "height_measure.py"), "py"),
            "体重测量": (os.path.join("scripts", "weight_measure.py"), "py"),
            "色觉检测": (os.path.join("scripts", "color", "dome.py"), "py")
        }

        # 图标映射表
        self.icon_map = {
            "血氧检测": "O₂",
            "视力检测": "👁️",
            "身高测量": "📏",
            "体重测量": "⏲️",
            "色觉检测": "🎨"
        }

        self.initUI()

    def initUI(self):
        # 主窗口布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)

        # 标题栏
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: #343a40; border-radius: 10px;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 10, 20, 10)

        title_label = QLabel("智能健康体检系统 (Linux版)")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        main_layout.addWidget(title_bar)

        # 功能卡片区域
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(25)
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)
        cards_layout.setColumnStretch(2, 1)

        # 创建功能卡片
        self.create_card(cards_layout, "血氧检测", 0, 0, "#FF6B6B", "#FF8E8E")
        self.create_card(cards_layout, "视力检测", 0, 1, "#4ECDC4", "#88D8C0")
        self.create_card(cards_layout, "身高测量", 0, 2, "#45B7D1", "#84D3EE")
        self.create_card(cards_layout, "体重测量", 1, 0, "#A37EBA", "#C7A4D6")
        self.create_card(cards_layout, "色觉检测", 1, 1, "#FFA07A", "#FFB88C")

        # 添加"更多功能"卡片
        empty_card = GradientFrame("#F8F9FA", "#F8F9FA")
        empty_card.setStyleSheet("border: 2px dashed #dee2e6; border-radius: 12px;")
        
        empty_layout = QVBoxLayout(empty_card)
        empty_layout.setContentsMargins(20, 20, 20, 20)
        empty_layout.setSpacing(15)
        
        # 添加水晶球图标
        icon_label = QLabel("🔮")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                color: #adb5bd;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 50px;
                padding: 20px;
            }
        """)
        icon_label.setFixedSize(80, 80)
        empty_layout.addWidget(icon_label, 0, Qt.AlignHCenter)
        
        # 添加文字
        text_label = QLabel("更多功能\n敬请期待")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        empty_layout.addWidget(text_label)
        
        cards_layout.addWidget(empty_card, 1, 2)

        main_layout.addWidget(cards_widget)

        # 添加底部状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #343a40;
                color: white;
                font-size: 12px;
            }
        """)
        self.statusBar().showMessage("系统就绪 | Linux版本")

    def create_card(self, layout, title, row, col, color1, color2):
        """创建渐变背景的功能卡片"""
        card = GradientFrame(color1, color2)
        card.setStyleSheet("border-radius: 12px;")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # 图标
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setText(self.icon_map.get(title, "?"))
        
        # 设置字体确保符号显示
        font = QFont()
        font.setFamilies(["Noto Color Emoji", "Symbola", "DejaVu Sans"])
        font.setPointSize(24)
        icon_label.setFont(font)
        
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                color: white;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 50px;
                padding: 20px;
            }
        """)
        icon_label.setFixedSize(80, 80)
        card_layout.addWidget(icon_label, 0, Qt.AlignHCenter)

        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
            }
        """)
        card_layout.addWidget(title_label)

        # 按钮
        btn = QPushButton("开始检测")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.9);
            }
        """)
        btn.clicked.connect(lambda: self.execute_linux_program(title))
        card_layout.addWidget(btn, 0, Qt.AlignHCenter)

        layout.addWidget(card, row, col)

    def execute_linux_program(self, title):
        """在Linux环境下执行程序"""
        program_info = self.program_map.get(title)
        if not program_info:
            self.statusBar().showMessage(f"错误: 未找到 {title} 的程序配置")
            return

        program_path, program_type = program_info
        abs_path = os.path.abspath(program_path)

        # 检查文件是否存在
        if not os.path.exists(abs_path):
            self.statusBar().showMessage(f"错误: 文件 {abs_path} 不存在")
            return

        # 检查执行权限
        if program_type == "exe" and not os.access(abs_path, os.X_OK):
            self.statusBar().showMessage(f"错误: 文件 {abs_path} 没有执行权限")
            return

        try:
            self.statusBar().showMessage(f"正在启动 {title} 检测...")

            # 获取程序所在目录
            program_dir = os.path.dirname(abs_path)

            if program_type == "py":
                subprocess.Popen([sys.executable, abs_path])
            else:
                subprocess.Popen([abs_path], cwd=program_dir)

            self.statusBar().showMessage(f"{title} 检测已启动 | PID: {os.getpid()}")

        except Exception as e:
            self.statusBar().showMessage(f"执行错误: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置Linux下更合适的字体
    font = QFont("Noto Sans CJK SC", 10)
    app.setFont(font)

    window = HealthCheckApp()
    window.show()
    sys.exit(app.exec_())