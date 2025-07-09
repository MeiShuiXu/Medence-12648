import sys
import serial
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush
from PyQt5.QtWidgets import QGraphicsOpacityEffect

os.environ["DISPLAY"] = ":0"

class WeightMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
        except serial.SerialException as e:
            QMessageBox.critical(self, "串口错误", f"无法打开串口:\n{str(e)}")
            sys.exit(1)

        self.setWindowTitle("高精度体重监测系统")
        self.setGeometry(100, 100, 1024, 768)
        self.setMinimumSize(600, 400)

        # 渐变背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(245, 247, 250))
        gradient.setColorAt(1, QColor(230, 235, 240))
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)

        # 标题
        title_label = QLabel("实时体重监测")
        title_font = QFont("微软雅黑", 28, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title_label)

        # 状态灯
        status_layout = QHBoxLayout()
        status_label = QLabel("设备状态:")
        status_label.setFont(QFont("微软雅黑", 14))
        status_label.setStyleSheet("color: #555;")

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)
        self.status_indicator.setStyleSheet("border-radius: 10px; background-color: #e74c3c;")

        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # 数值显示卡片
        value_card = QWidget()
        value_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        value_card.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
            padding: 40px;
        """)
        value_layout = QVBoxLayout(value_card)
        value_layout.setContentsMargins(20, 20, 20, 20)  # 增加内边距
        value_layout.setSpacing(10)

        # 数值标签
        self.value_label = QLabel("--")
        value_font = QFont("微软雅黑", 64, QFont.Bold)  # 减小字体大小
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #2980b9;")
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.value_label.setMinimumHeight(150)  # 设置最小高度

        # 应用透明度动画效果
        opacity_effect = QGraphicsOpacityEffect()
        self.value_label.setGraphicsEffect(opacity_effect)
        self.value_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.value_animation.setDuration(300)
        self.value_animation.setStartValue(0.0)
        self.value_animation.setEndValue(1.0)
        self.value_animation.setEasingCurve(QEasingCurve.InOutQuad)

        value_layout.addWidget(self.value_label, alignment=Qt.AlignCenter)

        # 单位标签
        unit_label = QLabel("单位: 克 (g)")
        unit_font = QFont("微软雅黑", 18)
        unit_label.setFont(unit_font)
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setStyleSheet("color: #7f8c8d;")
        value_layout.addWidget(unit_label, alignment=Qt.AlignCenter)

        layout.addWidget(value_card, stretch=1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("background-color: transparent; color: #555; font-size: 14px;")
        self.status_bar.showMessage("设备已连接，等待数据...")

        central_widget.setLayout(layout)

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_data)
        self.timer.start(100)

    def read_data(self):
        try:
            data = self.ser.read_all().decode('utf-8').strip()
            if data:
                self.status_indicator.setStyleSheet("border-radius: 10px; background-color: #2ecc71;")
                lines = [line for line in data.split('\n') if line]
                for line in lines:
                    if 'Weight:' in line:
                        try:
                            weight_str = line.split(':')[1].strip().split()[0]
                            weight = float(weight_str)
                            self.value_label.setText(f"{weight:.1f}")
                            self.value_animation.stop()
                            self.value_animation.start()
                            self.status_bar.showMessage(f"最后更新: {line.strip()}")
                        except (IndexError, ValueError) as e:
                            print(f"数据解析错误: {line} | {str(e)}")
        except Exception as e:
            self.status_indicator.setStyleSheet("border-radius: 10px; background-color: #e74c3c;")
            print(f"串口读取错误: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("微软雅黑", 12)
    app.setFont(font)
    window = WeightMonitor()
    window.show()
    sys.exit(app.exec_())