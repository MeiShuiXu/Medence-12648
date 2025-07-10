#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#include "OLED.h"
#include "Serial.h"
uint8_t RxData;			//定义用于接收串口数据的变量




void OLED_SetCursor(uint8_t Y, uint8_t X);
void OLED_WriteData(uint8_t Data);
// 16x16汉字字模库（紧凑型16字节格式）
const uint8_t OLED_F16x16[][32] = 
{
    // "身" 字
    {
        0x00,0x00,0x00,0xFC,0x54,0x56,0x55,0x54,
        0x54,0x54,0x54,0xFC,0x00,0x80,0x40,0x00,
        0x40,0x42,0x42,0x23,0x22,0x22,0x12,0x12,
        0x0A,0x46,0x82,0x7F,0x01,0x00,0x00,0x00
    },
    // "高" 字
    {
        0x04,0x04,0x04,0x04,0xF4,0x94,0x95,0x96,
        0x94,0x94,0xF4,0x04,0x04,0x04,0x04,0x00,
        0x00,0xFE,0x02,0x02,0x7A,0x4A,0x4A,0x4A,
        0x4A,0x4A,0x7A,0x02,0x82,0xFE,0x00,0x00
    }
};

/**
  * @brief  显示16x16汉字（自动处理分页）
  * @param  Line: 行号(1-4)
  * @param  Column: 列号(1-16) 
  * @param  Index: 汉字索引
  */
void Show_Chinese(uint8_t Line, uint8_t Column, uint8_t Index)
{
    uint8_t i;
    uint8_t page = (Line - 1) * 2;  // 计算页地址
    uint8_t col = (Column - 1) * 8; // 计算列地址
    
    // 上半部分（前8行）
    OLED_SetCursor(page, col);
    for(i = 0; i < 16; i++) {
        OLED_WriteData(OLED_F16x16[Index][i]);
    }
    
    // 下半部分（后8行）
    OLED_SetCursor(page + 1, col);
    for(i = 16; i < 32; i++) {
        OLED_WriteData(OLED_F16x16[Index][i]);
    }
}
int main(void)
{
	/*模块初始化*/
	OLED_Init();		//OLED初始化
	
	/*显示静态字符串*/
	OLED_ShowString(1, 1, "RxHex:");
	OLED_ShowString(2, 12, "cm");
	
	
	 // 显示"身高"汉字
    Show_Chinese(2, 1, 0);  // "身"
    Show_Chinese(2, 3, 1);  // "高"
    

	/*串口初始化*/
	Serial_Init();		//串口初始化
	
	Serial2_Init();  // UART2初始化
	

while (1)
{
    
    Serial_SendByte(0X55);  // 保留UART1发送
    
    RxData = Serial_GetRxData();  // 获取UART1接收的数据
    OLED_ShowHexNum(1, 7, RxData, 4);  // 显示十六进制
    OLED_ShowNum(2, 7, RxData/10, 4);  // 显示十进制
    
    // 通过UART2发送十进制数据
    //Serial2_SendNumber(RxData, 3);  // 发送3位十进制数（例如：123）
    Serial2_SendByte('\r');         // 添加回车符
    Serial2_SendByte('\n'); 	// 添加换行符
	float height = RxData;
	Serial2_Printf("height: %.1f cm", height/10.0);
	//Serial2_SendString(RxData);
	Delay_ms(500);
}
}