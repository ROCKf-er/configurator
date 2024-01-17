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
#include "constraints.h"


const uint16_t MAVLINK_MESSAGE_ID_STATUSTEXT = 253;
char STATUS_TEXT_SAVED[50];
char statustext[50];
char statustext_displayed[50];
bool status_saved_flag;

TFT_eSPI display = TFT_eSPI(DISP_HEIGHT, DISP_WIDTH); 
TFT_eSprite spr = TFT_eSprite(&display); // Invoke Sprite class
Parameters parameters;
uint32_t HB_count;

mavlink_param_value_t param_arr[PARAM_COUNT];
extern param_constraint param_costraint_arr[PARAM_COUNT];

uint16_t rol_index = 0;

const uint32_t HEARTBEAT_TIMEOUT_MS = 1000;
uint32_t heartbeat_last_time_ms = 0;

uint32_t msg_msgid = 0;

bool      heartbeat_received = false;
uint32_t  heartbeat_received_ms = 0;


void setup(){
  LOG_Serial.begin(115200);     // syslog 
  MAV_Serial.begin(57600);      // mavlink
  MAV_Serial.setPins(MAV_RX_PIN, MAV_TX_PIN);

  pinMode(LED_1_PIN, OUTPUT);
  pinMode(LED_2_PIN, OUTPUT);
  LED_1_ON;

  #ifdef DISPLAY_ON
    display.init();
    display.setRotation(1);
  #endif //DISPLAY_ON
    
  eeprom_init();
  eeprom_get();
  wifi_init();

  delay(500);

  update_parameters();

  strcpy(STATUS_TEXT_SAVED, "SAVED TO EEPROM");
  set_status_saved();
}


void send_heartbeat() {

  uint32_t now = millis();
  if (now - heartbeat_last_time_ms < HEARTBEAT_TIMEOUT_MS) {
    return;
  }
  heartbeat_last_time_ms = now;

  uint8_t mav_msg_buf[250];
  uint32_t mav_msg_len;
  mavlink_heartbeat_t com;
  mavlink_message_t message;

  //com.param_value = value;
  //com.target_system = 1;
  //com.target_component = MAV_COMP_ID_ALL;
  //memcpy(com.param_id, param_arr[index].param_id, 16);
  //com.param_type = param_arr[index].param_type;

  com.custom_mode = 15; /*<  A bitfield for use for autopilot-specific flags*/
  com.type = 1; /*<  Vehicle or component type. For a flight controller component the vehicle type (quadrotor, helicopter, etc.). For other components the component type (e.g. camera, gimbal, etc.). This should be used in preference to component id for identifying the component type.*/
  com.autopilot = 3; /*<  Autopilot type / class. Use MAV_AUTOPILOT_INVALID for components that are not flight controllers.*/
  com.base_mode = 217; /*<  System mode bitmap.*/
  com.system_status = 4; /*<  System status flag.*/
  com.mavlink_version = 3; 

  mavlink_msg_heartbeat_encode(SYSTEM_ID, COMPONENT_ID, &message, &com);
  mav_msg_len = mavlink_msg_to_send_buffer(mav_msg_buf, &message);
  
  MAV_Serial.write(mav_msg_buf, mav_msg_len); 

  if (heartbeat_received) {
    LED_2_TOGGLE; 
  } else {
    LED_2_OFF;
  }
}


void loop() {
  
  wifi_work();

  if (LOG_Serial.available()){              // Serial passthrough
    MAV_Serial.write(LOG_Serial.read());
  }

  mavlink_read(MAV_Serial); // Reading messages from quad

  #ifdef DISPLAY_ON
    
    spr.createSprite(DISP_WIDTH, DISP_HEIGHT); // Create sprite  
    spr.fillSprite(TFT_BLACK);

    spr.setTextSize(2); 
    spr.setTextColor(TFT_WHITE);
    spr.setCursor(10, 10);
    //spr.printf("HB seq: %d", HB_count);
    spr.printf("msg.msgid: %d", msg_msgid);
    spr.setCursor(10, 40);
    spr.printf("%d %s %0.3f", param_arr[10].param_index, param_arr[10].param_id, param_arr[10].param_value);
    spr.setCursor(10, 60);
    spr.printf("%d %s %0.3f", param_arr[11].param_index, param_arr[11].param_id, param_arr[11].param_value);
    spr.setCursor(10, 80);
    spr.printf("%d %s %0.3f", param_arr[12].param_index, param_arr[12].param_id, param_arr[12].param_value);
    spr.setCursor(10, 100);
    spr.printf("%d %s %0.3f", param_arr[13].param_index, param_arr[13].param_id, param_arr[13].param_value);

    spr.pushSprite(0, 0); // Push sprite to its position    

    delay(20);
  #endif //DISPLAY_ON

  send_heartbeat();
  if ((millis() - heartbeat_received_ms) > 5000) {
    heartbeat_received = false;
  }
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
  LOG_Serial.printf("Param_request\n");
}


bool mav_param_set(uint16_t index, float value){
  const uint8_t try_num = 5;
  uint8_t mav_msg_buf[250];
  uint32_t mav_msg_len;
  mavlink_param_set_t com;
  mavlink_message_t message;

  com.param_value = value;
  com.target_system = TARGET_SYSTEM;
  com.target_component = TARGET_COMPONENT;
  memcpy(com.param_id, param_arr[index].param_id, 16);
  com.param_type = param_arr[index].param_type;
  
  mavlink_msg_param_set_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
  mav_msg_len = mavlink_msg_to_send_buffer(mav_msg_buf, &message);

  for (uint8_t i = 0; i < try_num; i++) {
    MAV_Serial.write(mav_msg_buf, mav_msg_len); 
    delay(20);
    if (check_param(value, index)) {
      LOG_Serial.printf("SET %s %d: %.2f\n", param_arr[index].param_id, index, value);
      return true;
    } else {
      LOG_Serial.printf("SET %s %d: error\n", param_arr[index].param_id, index);
      return false;
    }
  }

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
  LOG_Serial.printf("Param request list\n");
}

void mav_param_request_read(uint16_t index){
  uint8_t mav_msg_buf[250];
  uint32_t mav_msg_len;
  mavlink_param_request_read_t com;
  mavlink_message_t message;

  com.target_component = TARGET_COMPONENT;
  com.target_system = TARGET_SYSTEM;
  com.param_index = index;

  mavlink_msg_param_request_read_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
  mav_msg_len = mavlink_msg_to_send_buffer(mav_msg_buf, &message);
  MAV_Serial.write(mav_msg_buf, mav_msg_len); 
}

void update_parameters(void){
  mav_param_request_list();                         //request for actual parameters
  for (auto &item: param_costraint_arr) {                      //filling an array with zerros  
    //item.param_value = 0.0;
    //memcpy(item.param_id, "##############\0", 16); 
    item.actual = false;
  }

  uint32_t now = millis();
  const uint32_t timeout = 1000;
  while((millis() - now) < timeout){                //waiting for new params
    mavlink_read(MAV_Serial);
  }
} 

bool check_param(float val, uint16_t index) {
  mavlink_status_t status;
  mavlink_message_t msg;
  mavlink_channel_t chan = MAVLINK_COMM_0;
  mavlink_param_value_t param;

  mav_param_request_read(index); 
  delay(10);
  while(MAV_Serial.available() > 0){
    uint8_t byte;
    MAV_Serial.readBytes(&byte, 1);

    if (mavlink_parse_char(chan, byte, &msg, &status) & (msg.msgid == MAVLINK_MSG_ID_PARAM_VALUE)) {
      mavlink_msg_param_value_decode(&msg, &param);
      return ((abs(param.param_value - val) < 0.00001) & (param.param_index == index));
    }
  }
}


void set_status_saved(void) {
  strcpy(statustext_displayed, "Saved     ");
  status_saved_flag = true;
}


void reset_status_saved(void) {
  strcpy(statustext_displayed, "Waiting...");
  status_saved_flag = false;
}

bool get_status_saved(void) {
  return status_saved_flag;
}


void mavlink_read(HardwareSerial &link){
  mavlink_status_t status;
  mavlink_message_t msg;
  mavlink_channel_t chan = MAVLINK_COMM_0;
  mavlink_param_value_t param;
  mavlink_param_request_read_t read_param;

  while(link.available() > 0){
    uint8_t byte;
    link.readBytes(&byte, 1);
    LOG_Serial.write(byte);   // Serial passthrough
        
    if (mavlink_parse_char(chan, byte, &msg, &status)) {
      msg_msgid = msg.msgid;

      switch (msg.msgid) {
        case MAVLINK_MSG_ID_PARAM_VALUE:  
          if (msg.compid == TARGET_COMPONENT) {
            mavlink_msg_param_value_decode(&msg, &param);
            param_arr[param.param_index] = param;
            param_costraint_arr[param.param_index].actual = true;
            LOG_Serial.printf("GET %d: %s = %.2f\n", param.param_index, param.param_id, param.param_value);
          }  
          break;
        case MAVLINK_MSG_ID_HEARTBEAT: 
          if (msg.compid == MAV_COMP_ID_ONBOARD_COMPUTER) {
            heartbeat_received = true;
            heartbeat_received_ms = millis();
          }
          break;
        case MAVLINK_MSG_ID_PARAM_REQUEST_READ:
          {
            /*
            mavlink_msg_param_request_read_decode(&msg, &read_param);          
            param = param_arr[read_param.param_index];
            mavlink_message_t message;
            mavlink_msg_param_value_encode(SYSTEM_ID,  MAV_COMP_ID_AUTOPILOT1, &message, &param);
            uint8_t mav_msg_resp_buf[250];
            uint16_t mav_msg_resp_len = mavlink_msg_to_send_buffer(mav_msg_resp_buf, &message);
            LOG_Serial.write(mav_msg_resp_buf, mav_msg_resp_len);             
            */
          }
          break;
        case MAVLINK_MSG_ID_PARAM_REQUEST_LIST:
          {/*
            mavlink_param_request_list_t param_request_list;
            mavlink_msg_param_request_list_decode(&msg, &param_request_list);
            for (uint16_t i = 0; i < param_arr[0].param_count; i++) {  
              mavlink_param_value_t param;
              param.param_count = param_arr[i].param_count;
              memcpy(param.param_id, param_arr[i].param_id, 16);
              param.param_index = param_arr[i].param_index;
              param.param_type = param_arr[i].param_type;
              param.param_value = param_arr[i].param_value;
              mavlink_message_t message;
              mavlink_msg_param_value_encode(SYSTEM_ID,  MAV_COMP_ID_AUTOPILOT1, &message, &param);
              uint8_t mav_msg_resp_buf[250];
              uint16_t mav_msg_resp_len = mavlink_msg_to_send_buffer(mav_msg_resp_buf, &message);
              LOG_Serial.write(mav_msg_resp_buf, mav_msg_resp_len);   
              //delay(500);
            }
          */
          }
          break;
        case MAVLINK_MESSAGE_ID_STATUSTEXT:
          {
            mavlink_msg_statustext_get_text(&msg, statustext);
            if (strcmp(statustext, STATUS_TEXT_SAVED) == 0) {
              set_status_saved();
            }

          }
          break;
        default: 
          break;
      }
    }
  }  
}


 