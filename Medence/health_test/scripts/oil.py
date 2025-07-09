import sys
import json
import random
import threading
import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QPainter

# MQTT 配置
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/combined"


class GradientFrame(QFrame):
    def __init__(self, color1, color2, parent=None):
        super().__init__(parent)
        self.color1 = QColor(color1)
        self.color2 = QColor(color2)
        self.setMinimumSize(250, 150)
        self.setStyleSheet("border-radius: 15px;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.color1)
        gradient.setColorAt(1, self.color2)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 15, 15)
        painter.end()


class HealthMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_mqtt()

        # 初始化数据
        self.bpm_simulated = 70
        self.has_received_data = False  # 标记是否收到过血氧和温度数据

    def setup_ui(self):
        self.setWindowTitle("智能健康监测系统")
        self.setFixedSize(950, 600)
        self.setStyleSheet("QMainWindow { background-color: #f5f7fa; }")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # 标题
        title = QLabel("智能健康监测系统")
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 28px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 数据卡片
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setSpacing(30)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        self.bpm_card = self.create_data_card("#ff6b6b", "#ff8e8e", "❤ 心率", "-- 次/分")
        self.spo2_card = self.create_data_card("#4ecdc4", "#88d8c0", "🩸 血氧", "-- %")
        self.temp_card = self.create_data_card("#45b7d1", "#84d3ee", "🌡 体温", "-- °C")

        cards_layout.addWidget(self.bpm_card)
        cards_layout.addWidget(self.spo2_card)
        cards_layout.addWidget(self.temp_card)
        main_layout.addWidget(cards_container)

        # 状态栏
        self.setup_status_bar(main_layout)

    def setup_status_bar(self, main_layout):
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet("""
            QFrame {
                background-color: #e8f4fc;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(20, 10, 20, 10)

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("font-size: 24px; color: gray;")
        self.status_label = QLabel("正在连接MQTT服务器...")
        self.status_label.setStyleSheet("font-size: 16px; color: #2c3e50;")

        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addWidget(self.status_bar)

    def setup_mqtt(self):
        # 设置线程异常处理
        threading.excepthook = self.handle_thread_exception

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # 启用日志和自动重连
        self.client.enable_logger()
        self.client.reconnect_delay_set(min_delay=1, max_delay=120)

        try:
            self.client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            self.update_status(f"连接失败: {str(e)}", "red")

    def handle_thread_exception(self, args):
        """处理线程异常"""
        print(f"线程异常: {args.exc_type.__name__}: {args.exc_value}")
        self.update_status("MQTT连接异常，尝试重连...", "red")
        self.client.reconnect()

    def create_data_card(self, color1, color2, title, value):
        card = GradientFrame(color1, color2)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        card_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
            }
        """)
        card_layout.addWidget(value_label, alignment=Qt.AlignCenter)
        card_layout.addStretch()

        if title == "❤ 心率":
            self.bpm_value = value_label
        elif title == "🩸 血氧":
            self.spo2_value = value_label
        elif title == "🌡 体温":
            self.temp_value = value_label

        return card

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.update_status("已连接到MQTT服务器", "green")
            client.subscribe(MQTT_TOPIC)
        else:
            self.update_status(f"连接失败（代码 {reason_code}）", "red")

    def on_disconnect(self, client, userdata, rc):
        self.update_status("MQTT连接断开，正在重连...", "red")

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode())

            # 更新血氧和温度数据
            spo2 = data.get("spo2", "--")
            temp = data.get("temp", "--")

            self.spo2_value.setText(f"{spo2} %")
            self.temp_value.setText(f"{float(temp):.1f} °C" if temp != "--" else "-- °C")

            # 只有当收到有效数据时才更新心率
            if spo2 != "--" and temp != "--":
                if not self.has_received_data:
                    # 第一次收到数据时初始化心率
                    self.has_received_data = True
                    self.update_heart_rate()
                else:
                    # 后续随机波动心率
                    delta = random.choice([-1, 0, 1])
                    self.bpm_simulated = max(65, min(75, self.bpm_simulated + delta))
                    self.bpm_value.setText(f"{self.bpm_simulated} 次/分")

        except Exception as e:
            print(f"消息处理错误: {e}")

    def update_heart_rate(self):
        """初始化心率显示"""
        self.bpm_value.setText(f"{self.bpm_simulated} 次/分")

    def update_status(self, text, color):
        colors = {"green": "#2ecc71", "red": "#e74c3c", "blue": "#3498db"}
        self.status_label.setText(text)
        self.status_indicator.setStyleSheet(f"font-size: 24px; color: {colors.get(color, 'gray')};")

    def closeEvent(self, event):
        self.client.disconnect()
        self.client.loop_stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))


    # 捕获未处理的异常
    def excepthook(exctype, value, traceback):
        print(f"未捕获异常: {exctype.__name__}: {value}")
        sys.exit(1)


    sys.excepthook = excepthook

    window = HealthMonitor()
    window.show()
    sys.exit(app.exec_())