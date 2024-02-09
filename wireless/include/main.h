#ifndef MAIN_H
#define MAIN_H

  #include <Arduino.h>

  #define MAV_RX_PIN 26
  #define MAV_TX_PIN 27
  #define LED_1_PIN 13
  #define LED_2_PIN 2

  #define TARGET_COMPONENT  MAV_COMP_ID_ONBOARD_COMPUTER
  #define TARGET_SYSTEM     1

  //#define DRONE_TYPE MAV_TYPE_HEXAROTOR
  #define DRONE_TYPE MAV_TYPE_FIXED_WING
  //#define DISPLAY_ON
  //#define DEBUG

  /*DRONE_TYPE == MAV_TYPE_FIXED_WING*/
    #define MODE_STABILIZE    0x02
    #define MODE_GUIDED_GPS   0x0F 
    #define MODE_GUIDED_NOGPS 0x14
  /************************************/

  #define LOG_Serial Serial
  #define MAV_Serial Serial1

  #define PARAM_COUNT 50
  #define UART_OK 0
  #define UART_TIMEOUT 2


  #define equal(a, b) (abs(a - b) < 0.0001)
  #define LED_1_ON      digitalWrite(LED_1_PIN, HIGH)
  #define LED_1_OFF     digitalWrite(LED_1_PIN, LOW)
  #define LED_1_TOGGLE  digitalWrite(LED_1_PIN, !digitalRead(LED_1_PIN))
  #define LED_2_ON      digitalWrite(LED_2_PIN, HIGH)
  #define LED_2_OFF     digitalWrite(LED_2_PIN, LOW)
  #define LED_2_TOGGLE  digitalWrite(LED_2_PIN, !digitalRead(LED_2_PIN))



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
    char bitmask[300];
  } param_constraint;
 
  void mavlink_read(uint8_t byte);
  void mav_param_request(uint16_t index);
  bool mav_param_set(uint16_t index, float value);
  void mav_param_request_list();
  void update_parameters(void);
  bool check_param(float val, uint16_t index);
  void set_status_saved(void);
  void reset_status_saved(void);
  bool get_status_saved(void);

#endif // MAIN_H 




