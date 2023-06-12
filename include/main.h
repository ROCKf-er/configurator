#ifndef MAIN_H
#define MAIN_H

  #include <Arduino.h>

  #define MAV_RX_PIN 26
  #define MAV_TX_PIN 27


  //#define DRONE_TYPE MAV_TYPE_HEXAROTOR
  #define DRONE_TYPE MAV_TYPE_FIXED_WING
  //#define PITCH_LOCK
  //#define DROP_MECHANISM
  //#define NEW_PROTOCOL
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
 
  #define SERVO_HZ 50 
  #define SERVO_MIN_PULSE 600  
  #define SERVO_MAX_PULSE 2400

  #define LOG_Serial Serial
  #define MAV_Serial Serial
  #define RAD_Serial Serial2

  #define UART_OK 0
  #define UART_TIMEOUT 2

  struct data_r
  {
    uint8_t xp;
    uint8_t ym;
    uint8_t yp;
    uint8_t xm;
    int16_t angle_x;
    int16_t angle_y;
    uint8_t byte_in;
    uint8_t level;
  };

  enum adjustment_type {
    LIN_TYPE,
    LOG_1_TYPE
  };

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

 
  void mavlink_read(HardwareSerial &link);
  void mav_param_request(uint16_t index);
  void mav_param_request_list();

#endif // MAIN_H 




