#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"

// ===== 网络配置 =====
const char* ssid = "没睡的iPhone";
const char* password = "xzx260039";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

// ===== 全局对象 =====
WiFiClient espClient;
PubSubClient client(espClient);
MAX30105 particleSensor;

// ===== 血氧参数 =====
#define BUFFER_LENGTH 100
uint32_t irBuffer[BUFFER_LENGTH];
uint32_t redBuffer[BUFFER_LENGTH];
int32_t spo2;
int8_t validSPO2;
int32_t heartRate;
int8_t validHeartRate;

// ===== MQTT增强参数 =====
#define MQTT_KEEPALIVE 60
const int MAX_MQTT_RETRIES = 7;
const unsigned long RECONNECT_BASE_DELAY = 1000;
unsigned long lastReconnectAttempt = 0;
int mqttRetryCount = 0;
bool criticalFailure = false;
unsigned long lastPublishTime = 0;
const long publishInterval = 2000;

// ===== 函数声明 =====
void setupWiFi();
void configureSensor();
void performMeasurement();
bool ensureMQTTConnection();
unsigned long getBackoffDelay();
String getMQTTError(int state);
void manageNetworkConnections();
void reconnectWiFi();
void blinkErrorLED(int count, int duration);

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  delay(100);

  setupWiFi();
  client.setServer(mqtt_server, mqtt_port);
  client.setKeepAlive(MQTT_KEEPALIVE);
  client.setSocketTimeout(15);

  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("未找到 MAX30105 传感器！");
    criticalFailure = true;
    return;
  }
  configureSensor();
  Serial.println("启动：仅检测 血氧 + 温度");
}

void loop() {
  if (criticalFailure) {
    blinkErrorLED(5, 500);
    return;
  }

  manageNetworkConnections();

  if (millis() - lastPublishTime > publishInterval) {
    performMeasurement();
    lastPublishTime = millis();
  }
}

// ===== 传感器配置 =====
void configureSensor() {
  particleSensor.softReset();
  particleSensor.setup(0x1F, 4, 2, 400, 411, 4096);
  particleSensor.clearFIFO();
  Serial.println("传感器初始化完成。");
}

// ===== 检测并发布数据 =====
void performMeasurement() {
  // 采集血氧数据
  for (int i = 0; i < BUFFER_LENGTH; i++) {
    while (!particleSensor.available()) particleSensor.check();
    redBuffer[i] = particleSensor.getRed();
    irBuffer[i] = particleSensor.getIR();
    particleSensor.nextSample();
  }

  maxim_heart_rate_and_oxygen_saturation(irBuffer, BUFFER_LENGTH, redBuffer,
                                         &spo2, &validSPO2, &heartRate, &validHeartRate);

  // 温度读取
  float temp = particleSensor.readTemperature();

  // 打印输出
  Serial.printf("SpO2: %d%%, Temp: %.2f°C\n", spo2, temp);

  // MQTT发布（心率字段设为0或省略）
  if (client.connected()) {
    char payload[128];
    snprintf(payload, sizeof(payload),
             "{\"bpm\":0,\"spo2\":%d,\"temp\":%.2f}",
             spo2, temp);
    client.publish("sensor/combined", payload);
  }
}

// ===== WiFi连接 =====
void setupWiFi() {
  Serial.print("连接WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("已连接！");
}

void reconnectWiFi() {
  Serial.println("重新连接WiFi...");
  WiFi.disconnect();
  WiFi.reconnect();

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(250);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi重新连接成功!");
    mqttRetryCount = 0;
  } else {
    Serial.println("\nWiFi重连失败!");
  }
}

// ===== MQTT连接管理 =====
bool ensureMQTTConnection() {
  if (client.connected()) return true;

  unsigned long now = millis();
  unsigned long backoffDelay = getBackoffDelay();

  if (now - lastReconnectAttempt > backoffDelay) {
    Serial.printf("尝试MQTT连接 (#%d)...", mqttRetryCount + 1);
    lastReconnectAttempt = now;

    String clientId = "ESP32-HEALTH-" + String(WiFi.macAddress());

    if (client.connect(clientId.c_str(), NULL, NULL,
                       "sensor/status", 1, true, "offline")) {
      Serial.println("成功!");
      client.publish("sensor/status", "online", true);
      mqttRetryCount = 0;
      return true;
    } else {
      int state = client.state();
      Serial.printf("失败! 错误码: %d - %s\n", state, getMQTTError(state).c_str());

      if (state == MQTT_CONNECT_BAD_PROTOCOL ||
          state == MQTT_CONNECT_BAD_CLIENT_ID) {
        criticalFailure = true;
        Serial.println("不可恢复的错误，停止尝试");
      }
      mqttRetryCount = min(mqttRetryCount + 1, MAX_MQTT_RETRIES);
    }
  }
  return false;
}

unsigned long getBackoffDelay() {
  unsigned long base = RECONNECT_BASE_DELAY * (1 << min(mqttRetryCount, 8));
  return base + random(0, 500);
}

String getMQTTError(int state) {
  switch (state) {
    case MQTT_CONNECTION_TIMEOUT:     return "连接超时";
    case MQTT_CONNECTION_LOST:        return "连接丢失";
    case MQTT_CONNECT_FAILED:         return "连接失败";
    case MQTT_DISCONNECTED:           return "连接断开";
    case MQTT_CONNECT_BAD_PROTOCOL:   return "协议错误";
    case MQTT_CONNECT_BAD_CLIENT_ID:  return "客户端ID无效";
    case MQTT_CONNECT_UNAVAILABLE:    return "服务不可用";
    case MQTT_CONNECT_BAD_CREDENTIALS:return "认证失败";
    case MQTT_CONNECT_UNAUTHORIZED:   return "未授权";
    default:                          return "未知错误";
  }
}

void manageNetworkConnections() {
  if (client.connected()) {
    client.loop();
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi连接丢失，尝试重连...");
    reconnectWiFi();
  }

  if (WiFi.status() == WL_CONNECTED && !client.connected()) {
    ensureMQTTConnection();
  }
}

// ===== 错误提示 =====
void blinkErrorLED(int count, int duration) {
  for (int i = 0; i < count; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(duration / 2);
    digitalWrite(LED_BUILTIN, LOW);
    delay(duration / 2);
  }
  delay(2000);
}

