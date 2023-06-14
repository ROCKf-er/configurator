#include <Arduino.h>
#include "main.h"
#include "data_display.h"
#include <SPI.h>
#include <Wire.h>
#include "mav_commands.h"
#include "filter.h"
#include "wifi_webserver.h"
#include <common/mavlink.h>
#include "_eeprom.h"
#include "PID.h"
#include <ESP32Servo.h>

#define TARGET_COMPONENT  191
#define TARGET_SYSTEM     1

TFT_eSPI display = TFT_eSPI(DISP_HEIGHT, DISP_WIDTH); 
TFT_eSprite spr = TFT_eSprite(&display); // Invoke Sprite class
Parameters parameters;
uint32_t HB_count;

mavlink_param_value_t param_arr[20];

uint16_t rol_index = 0;



void setup(){
  LOG_Serial.begin(115200);     // syslog 
  MAV_Serial.begin(57600);      // mavlink
  MAV_Serial.setPins(MAV_RX_PIN, MAV_TX_PIN);
  
  display.init();
  display.setRotation(1);
    
  eeprom_init();
  eeprom_get();
  wifi_init();

  delay(500);

  mav_param_request_list();
}




void loop() {
  
  wifi_work();

  mavlink_read(MAV_Serial); // Reading messages from quad

  param_arr[0].param_value += 1.0;
  
  spr.createSprite(DISP_WIDTH, DISP_HEIGHT); // Create sprite  
  spr.fillSprite(TFT_BLACK);

  spr.setTextSize(2); 
  spr.setTextColor(TFT_WHITE);
  spr.setCursor(10, 10);
  spr.printf("HB seq: %d", HB_count);
  spr.setCursor(10, 40);
  spr.printf("%d %s %0.3f", param_arr[0].param_index, param_arr[0].param_id, param_arr[0].param_value);
  spr.setCursor(10, 60);
  spr.printf("%d %s %0.3f", param_arr[1].param_index, param_arr[1].param_id, param_arr[1].param_value);
  spr.setCursor(10, 80);
  spr.printf("%d %s %0.3f", param_arr[2].param_index, param_arr[2].param_id, param_arr[2].param_value);
  spr.setCursor(10, 100);
  spr.printf("%d %s %0.3f", param_arr[3].param_index, param_arr[3].param_id, param_arr[3].param_value);

  spr.pushSprite(0, 0); // Push sprite to its position

  delay(20);

}



void mav_param_request(uint16_t index){
  uint8_t mav_msg_buf[250];
  uint32_t mav_msg_len;
  mavlink_param_request_read_t com;
  mavlink_message_t message;

  com.target_component = MAV_DEFAULT_TARG_COMPONENT;
  com.target_system = MAV_DEFAULT_TARG_SYS;
  com.param_index = index;

  mavlink_msg_param_request_read_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
  mav_msg_len = mavlink_msg_to_send_buffer(mav_msg_buf, &message);
  MAV_Serial.write(mav_msg_buf, mav_msg_len); 
}

void mav_param_request_list(){
  uint8_t mav_msg_buf[250];
  uint32_t mav_msg_len;
  mavlink_param_request_list_t com;
  mavlink_message_t message;

  com.target_component = TARGET_COMPONENT;
  com.target_system = TARGET_SYSTEM;

  mavlink_msg_param_request_list_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
  mav_msg_len = mavlink_msg_to_send_buffer(mav_msg_buf, &message);
  MAV_Serial.write(mav_msg_buf, mav_msg_len); 
}



void mavlink_read(HardwareSerial &link){
  mavlink_status_t status;
  mavlink_message_t msg;
  mavlink_channel_t chan = MAVLINK_COMM_0;
  mavlink_param_value_t param;

  while(link.available() > 0){
    uint8_t byte;
    link.readBytes(&byte, 1);
        
    if (mavlink_parse_char(chan, byte, &msg, &status)){
      switch (msg.msgid) {
        case MAVLINK_MSG_ID_PARAM_VALUE:  
          if (msg.compid == TARGET_COMPONENT) {
            mavlink_msg_param_value_decode(&msg, &param);
            param_arr[param.param_index] = param;
            LOG_Serial.printf("%d: %s = %.2f\n", param.param_index, param.param_id, param.param_value);
          }  
          break;
        case MAVLINK_MSG_ID_HEARTBEAT: 
          HB_count++;
          break;
        default: break;
      }

    }
  }  
}


 