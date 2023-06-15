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


 