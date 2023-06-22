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

TFT_eSPI display = TFT_eSPI(DISP_HEIGHT, DISP_WIDTH); 
TFT_eSprite spr = TFT_eSprite(&display); // Invoke Sprite class
Parameters parameters;
uint32_t HB_count;

mavlink_param_value_t param_arr[20];
param_constraint param_costraint_arr[20];

uint16_t rol_index = 0;

const uint32_t HEARTBEAT_TIMEOUT_MS = 1000;
uint32_t heartbeat_last_time_ms = 0;

uint32_t msg_msgid = 0;


void setup(){
  LOG_Serial.begin(115200);     // syslog 
  MAV_Serial.begin(57600);      // mavlink
  MAV_Serial.setPins(MAV_RX_PIN, MAV_TX_PIN);

  #ifdef DISPLAY_ON
    display.init();
    display.setRotation(1);
  #endif //DISPLAY_ON
    
  eeprom_init();
  eeprom_get();
  wifi_init();

  delay(500);

  update_parameters();

  int n;
  // G_ROLL_ANGLE
  n = 0;
  param_costraint_arr[n].min_value = -30;
  param_costraint_arr[n].max_value = 30;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = 25;
  strcpy(param_costraint_arr[n].description, "Кут крену при пошуку цілі (при RSSI < THRESHOLD)");
  // ANGLE_MIXER
  n = 1;
  param_costraint_arr[n].min_value = 0;
  param_costraint_arr[n].max_value = 1;
  param_costraint_arr[n].step_value = 0.01;
  param_costraint_arr[n].default_value = 0.5;
  strcpy(param_costraint_arr[n].description, "Відсоток від ROLL’у на руль повороту");
  // P_COEF
  n = 2;
  param_costraint_arr[n].min_value = 0.2;
  param_costraint_arr[n].max_value = 3;
  param_costraint_arr[n].step_value = 0.01;
  param_costraint_arr[n].default_value = 1.5;
  strcpy(param_costraint_arr[n].description, "Пропорційний коефіцієнт");
  // I_COEF
  n = 3;
  param_costraint_arr[n].min_value = 0;
  param_costraint_arr[n].max_value = 0.1;
  param_costraint_arr[n].step_value = 0.01;
  param_costraint_arr[n].default_value = 0;
  strcpy(param_costraint_arr[n].description, "Інтегральний коефіцієнт");
  // D_COEF
  n = 4;
  param_costraint_arr[n].min_value = 0;
  param_costraint_arr[n].max_value = 0.1;
  param_costraint_arr[n].step_value = 0.01;
  param_costraint_arr[n].default_value = 0;
  strcpy(param_costraint_arr[n].description, "Диференціальний коефіцієнт");
  // ANTENNA_ANGLE
  n = 5;
  param_costraint_arr[n].min_value = -90;
  param_costraint_arr[n].max_value = 90;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = -20;
  strcpy(param_costraint_arr[n].description, "Кут встановлення антенного модуля (-20º – нормаль антени відхилена вниз від осі літака)");
  // SERVO_CLOSE
  n = 6;
  param_costraint_arr[n].min_value = 1100;
  param_costraint_arr[n].max_value = 1900;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = 1900;
  strcpy(param_costraint_arr[n].description, "Сигнал на закриття скиду");
  // SERVO_OPEN
  n = 7;
  param_costraint_arr[n].min_value = 1100;
  param_costraint_arr[n].max_value = 1900;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = 1220;
  strcpy(param_costraint_arr[n].description, "Сигнал на відкриття скиду");
  // SERVO_CHANNEL
  n = 8;
  param_costraint_arr[n].min_value = 1;
  param_costraint_arr[n].max_value = 8;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = 7;
  strcpy(param_costraint_arr[n].description, "Номер каналу для підключення механізму скидання");
  // SCAN_ALT
  n = 9;
  param_costraint_arr[n].min_value = 100;
  param_costraint_arr[n].max_value = 400;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = 200;
  strcpy(param_costraint_arr[n].description, "Висота пошуку цілі");
  // SCAN_THRUST
  n = 10;
  param_costraint_arr[n].min_value = 0.3;
  param_costraint_arr[n].max_value = 1;
  param_costraint_arr[n].step_value = 0.01;
  param_costraint_arr[n].default_value = 0.4;
  strcpy(param_costraint_arr[n].description, "% газу при пошуку цілі");
  // DROP_ALT
  n = 11;
  param_costraint_arr[n].min_value = 50;
  param_costraint_arr[n].max_value = 200;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = 100;
  strcpy(param_costraint_arr[n].description, "Висота заходу на ціль");
  // DROP_LVL
  n = 12;
  param_costraint_arr[n].min_value = -80;
  param_costraint_arr[n].max_value = -50;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = -70;
  strcpy(param_costraint_arr[n].description, "Рівень сигналу при якому відбувається зниження до DROP_ALT");
  // DROP_THRUST
  n = 13;
  param_costraint_arr[n].min_value = 0.3;
  param_costraint_arr[n].max_value = 1;
  param_costraint_arr[n].step_value = 0.01;
  param_costraint_arr[n].default_value = 0.4;
  strcpy(param_costraint_arr[n].description, "% газу при заході на ціль");
  // DROP_ANGLE
  n = 14;
  param_costraint_arr[n].min_value = -90;
  param_costraint_arr[n].max_value = 0;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = -45;
  strcpy(param_costraint_arr[n].description, "Кут на ціль відносно літака, при якому скидається вантаж");
  // HEADING_APERTURE
  n = 15;
  param_costraint_arr[n].min_value = 1;
  param_costraint_arr[n].max_value = 360;
  param_costraint_arr[n].step_value = 1;
  param_costraint_arr[n].default_value = 360;
  strcpy(param_costraint_arr[n].description, "Після ввімкнення режиму Guided пошук цілі буде відбуватися у проміжку від (Heading –  HEADING_APERTURE / 2) до (Heading +  HEADING_APERTURE / 2)");
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
  
  LOG_Serial.write(mav_msg_buf, mav_msg_len); 
}


void loop() {
  
  wifi_work();

  mavlink_read(MAV_Serial); // Reading messages from quad
  //mavlink_read(LOG_Serial);

  //if (millis() % 2000 == 0)  mav_param_request_list();

  //param_arr[0].param_value += 1.0;

  #ifdef DISPLAY_ON
    
    spr.createSprite(DISP_WIDTH, DISP_HEIGHT); // Create sprite  
    spr.fillSprite(TFT_BLACK);

    spr.setTextSize(2); 
    spr.setTextColor(TFT_WHITE);
    spr.setCursor(10, 10);
    //spr.printf("HB seq: %d", HB_count);
    spr.printf("msg.msgid: %d", msg_msgid);
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
  #endif //DISPLAY_ON

  send_heartbeat();
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


void mav_param_set(uint16_t index, float value){
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
  MAV_Serial.write(mav_msg_buf, mav_msg_len); 
  LOG_Serial.printf("SET %d: %.2f\n", index, value);
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

void update_parameters(void){
  mav_param_request_list();                         //request for actual parameters
  for (auto &item: param_arr) {                      //filling an array with zerros  
    item.param_value = 0.0;
    memcpy(item.param_id, "##############\0", 16); 
  }

  uint32_t now = millis();
  const uint32_t timeout = 1000;
  while((millis() - now) < timeout){                //waiting for new params
    mavlink_read(MAV_Serial);
  }
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
        
    if (mavlink_parse_char(chan, byte, &msg, &status)){
      msg_msgid = msg.msgid;

      switch (msg.msgid) {
        case MAVLINK_MSG_ID_PARAM_VALUE:  
          if (msg.compid == TARGET_COMPONENT) {
            mavlink_msg_param_value_decode(&msg, &param);
            param_arr[param.param_index] = param;
            LOG_Serial.printf("GET %d: %s = %.2f\n", param.param_index, param.param_id, param.param_value);
          }  
          break;
        case MAVLINK_MSG_ID_HEARTBEAT: 
          HB_count++;
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
        default: 
          break;
      }
    }
  }  
}


 