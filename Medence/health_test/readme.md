# 健康体检一体机（Linux版）

## 项目简介

本项目是一套基于 Linux 平台的智能健康体检一体机软件，集成了血氧检测、视力检测、身高测量、体重测量、色觉检测等多项健康检测功能。主界面采用 PyQt5 实现，部分检测模块采用 OpenCV 和 C++ 实现，支持多种硬件设备的数据采集与可视化展示。

## 目录结构：
health_test/
├── main.py                 # 主控制界面程序（Python）
├── requirements.md         # 项目依赖说明文件（Markdown格式）
│
├── bin/                    # 可执行程序目录
│   ├── EyesTest            # 视力检测可执行程序（C++/OpenCV编译生成）
│   ├── EyesTest.cpp        # 视力检测C++源代码
│   └── SnellenChart/       # 视力检测图片资源目录
│       ├── 请闭上右眼.png  # 右眼检测提示图
│       ├── 请闭上左眼.png  # 左眼检测提示图
│       ├── 上.png          # 方向指示图（上）
│       ├── 下.png          # 方向指示图（下）
│       ├── 右.png          # 方向指示图（右）
│       └── 左.png          # 方向指示图（左）
│
└── scripts/                # 各检测模块脚本目录
    ├── height_measure.py   # 身高测量模块（Python）
    ├── weight_measure.py   # 体重测量模块（Python）
    ├── oil.py              # 血氧/体温/心率检测模块（通过MQTT协议通信）
    └── color/              # 色觉检测专用目录
        ├── dome.py         # 色觉检测主程序
        ├── 15.png          # 色觉检测图1（数字15）
        ├── 26.png          # 色觉检测图2（数字26）
        └── 369.png         # 色觉检测图3（数字369）

补充说明：
1. 主入口：main.py 负责整合所有检测模块
2. 硬件相关：
   - bin/EyesTest 需编译后使用
   - oil.py 依赖MQTT硬件设备
3. 资源文件：
   - SnellenChart/ 包含标准视力检测素材
   - color/ 包含色盲检测专用图片


## 功能说明

- **主界面**：入口为 [`main.py`](health_test/main.py)，集成所有检测功能，点击卡片启动对应检测程序。
- **血氧检测**：[`oil.py`](health_test/scripts/oil.py)，通过 MQTT 获取血氧、体温、心率数据，实时可视化。
- **视力检测**：[`EyesTest`](health_test/bin/EyesTest)，基于 OpenCV 图形界面，串口语音输入，自动判定视力等级。
- **身高测量**：[`height_measure.py`](health_test/scripts/height_measure.py)，串口读取身高仪数据。
- **体重测量**：[`weight_measure.py`](health_test/scripts/weight_measure.py)，串口读取体重仪数据。
- **色觉检测**：[`dome.py`](health_test/scripts/color/dome.py)，Ishihara 色盲测试，交互式答题。

## 运行环境

- **操作系统**：Linux（推荐 Ubuntu 20.04+）
- **Python**：3.8 及以上
- **依赖库**：
  - PyQt5
  - pyserial
  - paho-mqtt
  - opencv-python
  - numpy

- **C++依赖**（仅视力检测 EyesTest）：
  - g++ (支持 C++11)
  - OpenCV 4.x
  - iconv

## 安装依赖

```bash
# Python 依赖
pip install pyqt5 pyserial paho-mqtt 

# C++ 依赖（Ubuntu）
sudo apt-get install g++ libopencv-dev libiconv-hook-dev

#编译视力检查模块
cd health_test/bin
g++ EyesTest.cpp -o EyesTest $(pkg-config --cflags --libs opencv4) -std=c++11

#启动方法（在health_test目录下运行）
python3 main.py

#单独启动方法
python3 scripts/oil.py
python3 scripts/height_measure.py
python3 scripts/weight_measure.py
python3 scripts/color/dome.py
./bin/EyesTest

```
## 健康检测系统注意事项

### 硬件连接
- 确保所有硬件设备正确连接
- 串口参数(端口号、波特率等)需根据实际设备调整

### 视力检测要求
- 需要麦克风支持语音输入功能

### 文件管理
- 色觉检测和视力检测图片必须放置在指定目录：
