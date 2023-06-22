#ifndef MAIN_H
#define MAIN_H

  #include <Arduino.h>

  #define MAV_RX_PIN 26
  #define MAV_TX_PIN 27

  #define TARGET_COMPONENT  MAV_COMP_ID_ONBOARD_COMPUTER
  #define TARGET_SYSTEM     1

  //#define DRONE_TYPE MAV_TYPE_HEXAROTOR
  #define DRONE_TYPE MAV_TYPE_FIXED_WING
  #define DISPLAY_ON
  //#define DEBUG

  /*DRONE_TYPE == MAV_TYPE_FIXED_WING*/
    #define MODE_STABILIZE    0x02
    #define MODE_GUIDED_GPS   0x0F 
    #define MODE_GUIDED_NOGPS 0x14
  /************************************/


  /*DRONE_TYPE == MAV_TYPE_HEXAROTOR
    #define MODE_STABILIZE    0x00
    #define MODE_AUTO         0x03
    #define MODE_GUIDED_GPS   0x04 
    #define MODE_GUIDED_NOGPS 0x14
  *********************************/

  #define LOG_Serial Serial
  #define MAV_Serial Serial1
  #define RAD_Serial Serial2

  #define UART_OK 0
  #define UART_TIMEOUT 2


  struct Parameters{
    uint16_t threshold_lvl;
    uint16_t mav_msg_rate_ms;
    float steering_max_speed;
    float steering_speed_coef;
    float max_angle;
    float angle_coef;
    uint16_t min_servo_pulse;
    uint16_t max_servo_pulse;
    int16_t lead_angle;
  };

  typedef struct {
    float min_value;
    float max_value;
    float step_value;
    float default_value;
    char description[300];
    bool actual;
  } param_constraint;
 
  void mavlink_read(HardwareSerial &link);
  void mav_param_request(uint16_t index);
  void mav_param_set(uint16_t index, float value);
  void mav_param_request_list();
  void update_parameters(void);

#endif // MAIN_H 




