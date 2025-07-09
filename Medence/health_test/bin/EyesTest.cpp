#include <iostream>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <vector>
#include <cstring>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/select.h>
#include <iconv.h>
#include <opencv2/opencv.hpp>

// 串口初始化函数
int init_uart(const char* dev = "/dev/ttyS9")
{
    int fd = open(dev, O_RDWR | O_NOCTTY | O_NDELAY);
    if (fd < 0) {
        perror("open");
        return -1;
    }
    struct termios newtio;
    bzero(&newtio, sizeof(newtio));
    newtio.c_cflag |= CLOCAL | CREAD;
    newtio.c_cflag &= ~CSIZE;
    newtio.c_cflag |= CS8;
    newtio.c_cflag &= ~PARENB;
    cfsetispeed(&newtio, B9600);
    cfsetospeed(&newtio, B9600);
    newtio.c_cflag &= ~CSTOPB;
    newtio.c_cc[VTIME] = 0;
    newtio.c_cc[VMIN] = 0;
    tcflush(fd, TCIFLUSH);
    if ((tcsetattr(fd, TCSANOW, &newtio)) != 0) {
        perror("com set error");
        close(fd);
        return -1;
    }
    return fd;
}

// 串口接收
int uart_read_frame(int fd, unsigned char *p_receive_buff, int count, int timeout_data)
{
    int nread = 0;
    fd_set rd;
    int retval = 0;
    struct timeval timeout = {0, timeout_data*1000};
    FD_ZERO(&rd);
    FD_SET(fd, &rd);
    memset(p_receive_buff, 0x0, count);
    retval = select(fd + 1, &rd, NULL, NULL, &timeout);
    switch (retval)
    {
        case 0:
            nread = 0;
            break;
        case -1:
            printf("select%s\n", strerror(errno));
            nread = -1;
            break;
        default:
            nread = read(fd, p_receive_buff, count-1); // 留一个字节给\0
            break;
    }
    if (nread > 0) p_receive_buff[nread] = '\0'; // 保证字符串结束
    return nread;
}

// GBK转UTF-8函数
void gbk_to_utf8(const char* gbk, char* utf8, size_t utf8_len) {
    iconv_t cd = iconv_open("UTF-8", "GBK");
    if (cd == (iconv_t)-1) {
        utf8[0] = '\0';
        return;
    }
    size_t inlen = strlen(gbk);
    char* inbuf = (char*)gbk;
    char* outbuf = utf8;
    size_t outlen = utf8_len - 1;
    iconv(cd, &inbuf, &inlen, &outbuf, &outlen);
    *outbuf = '\0';
    iconv_close(cd);
}

char* read_uart_data(int fd, int timeout_ms) {
    unsigned char buffer[256];
    int n = uart_read_frame(fd, buffer, sizeof(buffer), timeout_ms);
    
    if (n <= 0) {
        return nullptr;
    }
    // 打印原始数据(调试用)
    //printf("原始数据: ");
    //for (int i = 0; i < n; ++i) printf("%02X ", buffer[i]);
    //printf("\n");
    char* utf8buf = (char*)malloc(512);
    if (!utf8buf) {
        return nullptr;
    }
    memset(utf8buf, 0, 512);
    // 判断是否为FD开头的协议包
    if (buffer[0] == 0xFD && n > 9) {
        gbk_to_utf8((char*)(buffer + n - 9), utf8buf, 512);
    } else {
        gbk_to_utf8((char*)buffer, utf8buf, 512);
    }

    return utf8buf;
}


char* read_from_uart(int fd) {
    char* received_data = nullptr;  // 初始化为 nullptr

    while (true) {
        char* new_data = read_uart_data(fd, 100);  // 100ms 超时
        if (new_data) {
            if (received_data) free(received_data);  // 释放旧数据（如果有）
            received_data = new_data;  // 保存新数据
            break;
        }
    }

    return received_data;
}


// 函数：按比例缩放图片并在固定窗口中显示（空白部分用白色填充）
void displayScaledImage(const cv::Mat& image, double scale, const std::string& windowName, int windowWidth, int windowHeight) {
    if (image.empty()) {
        std::cerr << "Error: Input image is empty!" << std::endl;
        return;
    }
    // 计算缩放后的尺寸（保持原比例）
    int newWidth = static_cast<int>(image.cols * scale);
    int newHeight = static_cast<int>(image.rows * scale);
    // 等比例缩放图片
    cv::Mat resizedImage;
    cv::resize(image, resizedImage, cv::Size(newWidth, newHeight), 0, 0, cv::INTER_AREA);
    // 创建固定大小的白色背景
    cv::Mat displayImage(windowHeight, windowWidth, image.type(), cv::Scalar(255, 255, 255));
    // 计算居中位置
    int xOffset = (windowWidth - newWidth) / 2;
    int yOffset = (windowHeight - newHeight) / 2;
    // 确保缩放后的图片不会超出窗口边界
    if (xOffset >= 0 && yOffset >= 0 && (xOffset + newWidth) <= windowWidth && (yOffset + newHeight) <= windowHeight) {
        // 将缩放后的图片复制到白色背景的中央
        cv::Rect roi(xOffset, yOffset, newWidth, newHeight);
        resizedImage.copyTo(displayImage(roi));
    } else {
        std::cerr << "Error: Scaled image exceeds window dimensions!" << std::endl;
        return;
    }
    // 创建窗口并显示图片
    cv::namedWindow(windowName, cv::WINDOW_AUTOSIZE);
    cv::imshow(windowName, displayImage);
}

void displayVision(const char* leftEye, const char* rightEye) {
    // 创建高清画布 (800x600)
    cv::Mat image(600, 800, CV_8UC3);
    
    // 蓝色渐变背景 (从浅蓝到深蓝)
    for (int y = 0; y < image.rows; y++) {
        float ratio = static_cast<float>(y) / image.rows;
        cv::line(image, cv::Point(0, y), cv::Point(image.cols, y),
               cv::Scalar(240 - ratio*100, 245 - ratio*120, 255 - ratio*50));
    }
    
    // 添加半透明面板
    cv::Mat panel(image, cv::Rect(50, 50, 700, 500));
    cv::Mat glass = panel.clone();
    cv::GaussianBlur(glass, glass, cv::Size(55, 55), 0);
    cv::addWeighted(panel, 0.3, glass, 0.7, 0, panel);
    cv::rectangle(image, cv::Rect(50, 50, 700, 500), 
                cv::Scalar(255, 255, 255), 2, cv::LINE_AA);
    
    // 设置多级字体样式
    int titleFont = cv::FONT_HERSHEY_DUPLEX;
    int headerFont = cv::FONT_HERSHEY_SIMPLEX;
    int valueFont = cv::FONT_HERSHEY_COMPLEX;
    
    // 主标题
    cv::putText(image, "VISION TEST REPORT", cv::Point(100, 120), 
               titleFont, 1.5, cv::Scalar(10, 30, 80), 2, cv::LINE_AA);
    
    // 副标题线
    cv::line(image, cv::Point(100, 140), cv::Point(700, 140), 
            cv::Scalar(200, 200, 255), 2, cv::LINE_AA);
    
    // 视力数据展示区
    const int y_start = 220;
    const int x_label = 150;
    const int x_value = 500;
    
    // 左眼视力
    cv::putText(image, "LEFT EYE:", cv::Point(x_label, y_start), 
               headerFont, 1.0, cv::Scalar(80, 80, 80), 1, cv::LINE_AA);
    cv::putText(image, leftEye, cv::Point(x_value, y_start), 
               valueFont, 1.2, cv::Scalar(0, 100, 200), 2, cv::LINE_AA);
    
    // 右眼视力
    cv::putText(image, "RIGHT EYE:", cv::Point(x_label, y_start+100), 
               headerFont, 1.0, cv::Scalar(80, 80, 80), 1, cv::LINE_AA);
    cv::putText(image, rightEye, cv::Point(x_value, y_start+100), 
               valueFont, 1.2, cv::Scalar(0, 100, 200), 2, cv::LINE_AA);
    
    // 添加视力评估标签
    std::string assessment = (atof(rightEye) >= 1.0 || atof(leftEye) >= 1.0) ?
                           "NORMAL VISION" : "RECOMMEND FURTHER EXAMINATION";
    cv::Scalar assessmentColor = (assessment[0] == 'N') ? 
                               cv::Scalar(0, 180, 0) : cv::Scalar(0, 100, 255);
    
    cv::putText(image, assessment, cv::Point(150, 450), 
               valueFont, 1.0, assessmentColor, 2, cv::LINE_AA);
    
    // 添加装饰性元素
    cv::ellipse(image, cv::Point(150, 380), cv::Size(60, 30), 
               0, 0, 180, cv::Scalar(200, 200, 255), 3, cv::LINE_AA);
    cv::ellipse(image, cv::Point(650, 380), cv::Size(60, 30), 
               0, 180, 360, cv::Scalar(200, 200, 255), 3, cv::LINE_AA);
    
    // 底部信息
    cv::putText(image, "Generated by VisionCheck Pro", cv::Point(200, 550), 
               cv::FONT_HERSHEY_SCRIPT_SIMPLEX, 1.2, cv::Scalar(150, 150, 150), 1);
    
    // 显示窗口
    cv::namedWindow("Vision Test System", cv::WINDOW_NORMAL);
    cv::resizeWindow("Vision Test System", 800, 600);
    cv::imshow("Vision Test System", image);
    cv::waitKey(0);
}

int main() {
    //if (argc < 2) {
    //    std::cerr << "用法: " << argv[0] << " /dev/ttyS9" << std::endl;
    //    return -1;
    //}

    // 初始化串口
    //int fd = init_uart(argv[1]);
    int fd = init_uart();
    if (fd < 0) return -1;

    // 设置窗口大小
    const int windowWidth = 950;
    const int windowHeight = 600;

    // 定义图片路径（应该放在文件头部全局区域）
    const char* eyes[] = {"SnellenChart/请闭上右眼.png", "SnellenChart/请闭上左眼.png"};
    const char* direction[] = {"SnellenChart/上.png", "SnellenChart/下.png", 
                        "SnellenChart/左.png", "SnellenChart/右.png"};

    // 答案
    const char* answer[] = {"上", "下", "左", "右"};

    // 比例
    double image_size[] = {1.0, 0.8, 0.6, 0.4, 0.2};

    // 视力结果
    //double result[] = {0.4, 0.6, 0.8, 1.0, 1.2};
    const char* result[] = {"0.4", "0.6", "0.8", "1.0", "1.2"};
    //double left = 1.2, right = 1.2;
    const char* left = "1.2";
    const char* right = "1.2";
    
    // 左右眼睛
    for(int i = 0; i < 2; i++){

        // 测量左右眼睛
        cv::Mat image_eye = cv::imread(eyes[i]);
        displayScaledImage(image_eye, 1.0, "Eyes Test",  windowWidth, windowHeight);
        cv::waitKey(3000);
        cv::destroyAllWindows();

        int index = -1;

        // 大小
        for(int j = 0; j < 5; j++){

            // 判断正确的结果
            int ans = 0;

            // 方向
            for(int z = 0; z < 4; z++){

                // 随机播放图片,前一张图片和后一张不一样
                int current_index;
                do{
                    current_index = rand() % 4; // 随机选择一个索引
                }while(current_index == index);
                index = current_index;

                // 图片
                cv::Mat image_direction = cv::imread(direction[index]);

                // 显示当前测量的方向
                displayScaledImage(image_direction, image_size[j], "Eyes Test", windowWidth, windowHeight);
                cv::waitKey(3000);

                // 接受语音
                char* received_data = read_from_uart(fd);

                // 判断
                if (strstr(received_data, answer[index]) != NULL) {
                    printf("判断正确\n");
                    ans++ ;
                    free(received_data);
                }
                cv::destroyAllWindows();
            }
            // printf("当前测量的视力为：%.1lf\n", atof(result[j]));
            if (ans < 3){
                if (i == 0){
                    left = result[j];// 左眼
                }else{
                    right = result[j];// 右眼
                }
                break;
            }
        }
    }
    //printf("视力检查结果\n左眼：%.1lf\n右眼：%.1lf\n", left, right);
    printf("视力检查结果\n左眼：%s\n右眼：%s\n", left, right);
    // 显示视力结果
    displayVision(left, right);
    close(fd);
    return 0;
}
//g++ EyesTest.cpp -o EyesTest $(pkg-config --cflags --libs opencv4) -std=c++11
