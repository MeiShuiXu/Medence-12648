import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                            QPushButton, QVBoxLayout, QHBoxLayout, QFrame, 
                            QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QCoreApplication

# 必须在创建QApplication前设置高DPI缩放
QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

class ColorVisionTest(QMainWindow):
    def __init__(self):
        super().__init__()
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'
        
        self.setWindowTitle("色觉测试系统 - Linux版")
        self.setFixedSize(950, 550)
        
        self.current_test = 0
        self.score = 0
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.tests = [
            {"image": os.path.join(self.script_dir, "15.png"), "correct": "15", "options": ["1", "5", "15"]},
            {"image": os.path.join(self.script_dir, "26.png"), "correct": "26", "options": ["2", "6", "26"]},
            {"image": os.path.join(self.script_dir, "369.png"), "correct": "369", "options": ["3", "6", "9", "369"]}
        ]

        self.font_family = self.init_fonts()
        self.init_ui()
        self.load_test()
    
    def init_fonts(self):
        # 尝试加载Linux常用中文字体
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc"
        ]
        
        loaded_fonts = []
        for font_path in font_paths:
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    loaded_fonts.extend(QFontDatabase.applicationFontFamilies(font_id))
        
        # 优先选择支持中文的字体
        preferred_fonts = ["WenQuanYi Micro Hei", "Noto Sans CJK SC", 
                         "AR PL UMing CN", "DejaVu Sans", "Sans Serif"]
        
        for font in preferred_fonts:
            if font in loaded_fonts or font in QFontDatabase().families():
                return font
        
        return "Sans Serif"  # 最终回退
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题标签
        self.title_label = QLabel("请选择图片中显示的数字")
        self.title_label.setFont(QFont(self.font_family, 18, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(self.title_label)
        
        # 图片显示区域
        self.image_frame = QFrame()
        self.image_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #bdc3c7;
                padding: 10px;
            }
        """)
        self.image_frame.setFixedSize(520, 370)
        
        self.image_layout = QVBoxLayout(self.image_frame)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(500, 350)
        self.image_layout.addWidget(self.image_label)
        main_layout.addWidget(self.image_frame, alignment=Qt.AlignCenter)
        
        # 选项按钮区域
        self.options_frame = QFrame()
        self.options_layout = QHBoxLayout()
        self.options_layout.setSpacing(20)
        self.options_layout.setContentsMargins(20, 30, 20, 20)
        self.options_frame.setLayout(self.options_layout)
        main_layout.addWidget(self.options_frame, alignment=Qt.AlignCenter)
        
        main_layout.addStretch(1)
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #f5f7fa;
            }}
            QLabel {{
                font-family: "{self.font_family}";
            }}
            QPushButton {{
                font-family: "{self.font_family}";
                font-size: 16px;
                font-weight: bold;
                min-width: 100px;
                min-height: 50px;
                border-radius: 8px;
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:pressed {{
                background-color: #1a5276;
            }}
        """)
    
    def load_test(self):
        if self.current_test < len(self.tests):
            test = self.tests[self.current_test]
            self.title_label.setText(f"测试 {self.current_test + 1}/{len(self.tests)}: 请选择图片中显示的数字")
            
            if os.path.exists(test["image"]):
                pixmap = QPixmap(test["image"])
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap.scaled(
                        500, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    ))
                else:
                    self.image_label.setText(f"图片加载失败: {os.path.basename(test['image'])}")
                    self.image_label.setStyleSheet("color: red; font-size: 14px;")
            else:
                self.image_label.setText(f"文件不存在: {test['image']}")
                self.image_label.setStyleSheet("color: red; font-size: 14px;")
            
            for i in reversed(range(self.options_layout.count())): 
                self.options_layout.itemAt(i).widget().deleteLater()
            
            for option in test["options"]:
                btn = QPushButton(option)
                btn.setFixedSize(120, 60)
                btn.clicked.connect(lambda checked, opt=option: self.check_answer(opt))
                self.options_layout.addWidget(btn)
        else:
            self.show_result()
    
    def check_answer(self, selected):
        test = self.tests[self.current_test]
        if selected == test["correct"]:
            self.score += 1
        self.current_test += 1
        self.load_test()
    
    def show_result(self):
        result_widget = QWidget()
        result_layout = QVBoxLayout()
        result_widget.setLayout(result_layout)
        self.setCentralWidget(result_widget)
        
        result_text = f"测试完成！\n\n您的得分: {self.score}/{len(self.tests)}"
        color = "#27ae60" if self.score >= 2 else "#e74c3c"
        
        result_label = QLabel(result_text)
        result_label.setFont(QFont(self.font_family, 20, QFont.Bold))
        result_label.setStyleSheet(f"color: {color};")
        result_label.setAlignment(Qt.AlignCenter)
        result_label.setWordWrap(True)
        result_layout.addWidget(result_label)
        
        diagnosis = QLabel()
        diagnosis.setFont(QFont(self.font_family, 14))
        diagnosis.setAlignment(Qt.AlignCenter)
        diagnosis.setWordWrap(True)
        
        if self.score >= 2:
            diagnosis.setText("您的色觉正常")
            diagnosis.setStyleSheet("color: #27ae60;")
        else:
            diagnosis.setText("您可能存在色觉异常\n\n注意: 此测试仅为初步筛查，\n专业诊断请咨询眼科医生")
            diagnosis.setStyleSheet("color: #e74c3c;")
        
        result_layout.addWidget(diagnosis)
        
        exit_btn = QPushButton("完成")
        exit_btn.setFixedSize(200, 60)
        exit_btn.clicked.connect(self.close)
        result_layout.addWidget(exit_btn, alignment=Qt.AlignCenter)
        
        result_layout.addStretch(1)
        result_layout.setSpacing(20)
        result_layout.setContentsMargins(40, 40, 40, 40)

if __name__ == "__main__":
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'
    
    app = QApplication(sys.argv)
    window = ColorVisionTest()
    window.show()
    sys.exit(app.exec_())