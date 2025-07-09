import sys
import serial
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                            QPushButton, QVBoxLayout, QHBoxLayout, QFrame, 
                            QStatusBar, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, QDateTime, QCoreApplication
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush

os.environ["DISPLAY"] = ":0"

class HeightMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        # 串口初始化
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
            self.connected = True
        except serial.SerialException as e:
            QMessageBox.critical(self, "串口错误", f"无法打开串口:\n{str(e)}")
            sys.exit(1)

        # 界面设置
        self.setWindowTitle("身高监测系统 - 专业版")
        self.setFixedSize(960, 530)  # 固定窗口大小
        
        # 设置现代UI风格
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #f5f7fa, stop:1 #c3cfe2);
            }
            QLabel#title {
                color: #2c3e50;
                font-size: 28px;
                font-weight: bold;
                padding: 10px;
            }
            QFrame#dataFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #dfe6e9;
            }
            QStatusBar {
                background: rgba(255, 255, 255, 150);
                color: #2d3436;
                font-size: 12px;
                border-top: 1px solid #b2bec3;
            }
        """)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 20)
        main_layout.setSpacing(30)

        # 标题区
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("身高监测系统")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.title_label)
        
        # 添加装饰线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("border: 1px solid #b2bec3;")
        title_layout.addWidget(line)
        
        main_layout.addWidget(title_frame)

        # 状态指示区
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        # 状态标签
        status_label = QLabel("设备状态:")
        status_label.setStyleSheet("""
            font-size: 14px;
            color: #636e72;
            font-weight: bold;
        """)
        status_layout.addWidget(status_label)
        
        # 状态指示灯
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("""
            background-color: #2ecc71;
            border-radius: 8px;
            border: 1px solid #27ae60;
        """)
        status_layout.addWidget(self.status_indicator)
        
        # 时间显示
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            font-size: 13px;
            color: #636e72;
            font-family: 'Arial';
        """)
        status_layout.addStretch()
        status_layout.addWidget(self.time_label)
        
        main_layout.addWidget(status_frame)

        # 身高数据显示区
        data_frame = QFrame()
        data_frame.setObjectName("dataFrame")
        data_frame.setFixedHeight(300)
        data_layout = QVBoxLayout(data_frame)
        data_layout.setContentsMargins(30, 30, 30, 30)
        data_layout.setSpacing(20)
        
        # 数值显示
        self.height_value = QLabel("--")
        self.height_value.setStyleSheet("""
            font-size: 100px;
            font-weight: bold;
            color: #0984e3;
            qproperty-alignment: AlignCenter;
        """)
        data_layout.addWidget(self.height_value, 1)
        
        # 单位标签
        unit_label = QLabel("厘米 (cm)")
        unit_label.setStyleSheet("""
            font-size: 22px;
            color: #636e72;
            qproperty-alignment: AlignCenter;
        """)
        data_layout.addWidget(unit_label)
        
        main_layout.addWidget(data_frame, 1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                padding: 5px;
            }
            QStatusBar::item {
                border: none;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("系统已就绪，等待身高数据...")

        # 添加版本信息
        version_label = QLabel("v1.0.0 专业医疗版")
        version_label.setStyleSheet("color: #636e72; font-size: 10px;")
        self.status_bar.addPermanentWidget(version_label)

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_data)
        self.timer.start(100)

        # 初始化时间
        self.update_time()

    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.time_label.setText(current_time)

    def read_data(self):
        if not self.connected:
            return

        try:
            data = self.ser.read_all().decode('utf-8', errors='ignore').strip()
            if data:
                self.update_time()
                self.status_indicator.setStyleSheet("""
                    background-color: #00b894;
                    border-radius: 8px;
                    border: 1px solid #00a884;
                """)

                # 解析height: X.X cm格式的数据
                if "height" in data.lower() and "cm" in data.lower():
                    try:
                        start_idx = data.lower().find(":") + 1
                        end_idx = data.lower().find("cm")
                        if start_idx < end_idx:
                            value_str = data[start_idx:end_idx].strip()
                            height = float(value_str)
                            self.height_value.setText(f"<b>{height:.1f}</b>")
                            self.status_bar.showMessage(f"最新数据: 身高 {height:.1f} cm | 数据接收正常")
                            
                            # 数值变化动画效果
                            self.height_value.setStyleSheet(f"""
                                font-size: 100px;
                                font-weight: bold;
                                color: #0984e3;
                                qproperty-alignment: AlignCenter;
                                border-bottom: 2px solid #74b9ff;
                            """)
                        else:
                            self.status_bar.showMessage(f"数据格式异常: {data}")
                    except (ValueError, IndexError) as e:
                        self.status_bar.showMessage(f"数据解析失败: {data} ({str(e)})")
                        self.status_indicator.setStyleSheet("""
                            background-color: #fdcb6e;
                            border-radius: 8px;
                            border: 1px solid #e17055;
                        """)
                else:
                    self.status_bar.showMessage(f"未识别数据格式: {data}")

        except Exception as e:
            self.status_indicator.setStyleSheet("""
                background-color: #d63031;
                border-radius: 8px;
                border: 1px solid #c0392b;
            """)
            self.status_bar.showMessage(f"通信错误: {str(e)}")
            self.connected = False

if __name__ == "__main__":
    # 设置高DPI缩放
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10) if sys.platform == "linux" else QFont("Arial", 10)
    app.setFont(font)
    
    window = HeightMonitor()
    window.show()
    sys.exit(app.exec_())