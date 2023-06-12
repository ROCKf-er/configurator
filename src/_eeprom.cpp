#include "main.h"
#include "_eeprom.h"
#include <EEPROM.h>

extern Parameters parameters;

void eeprom_init(){
    EEPROM.begin(EEPROM_SIZE);
    if (EEPROM.read(0) != INIT_KEY) {eeprom_set_default();}
}

void eeprom_set_default() {
    EEPROM.put(0, INIT_KEY);
    parameters.threshold_lvl =  THRESHOLD_LVL_DEFAULT;
    parameters.mav_msg_rate_ms = MAV_MSG_RATE_MS_DEFAULT;
    parameters.steering_max_speed = STEERING_MAX_SPEED_DEFAULT;
    parameters.steering_speed_coef = STEERING_SPEED_COEF_DEFAULT;
    parameters.max_angle = MAX_ANGLE_DEFAULT;
    parameters.angle_coef = ANGLE_COEF_DEFAULT;  
    parameters.min_servo_pulse = MIN_SERVO_PULSE_DEFAULT;  
    parameters.max_servo_pulse = MAX_SERVO_PULSE_DEFAULT;  
    parameters.lead_angle = LEAD_ANGLE_DEFAULT;  
    EEPROM.put(1, parameters);
    EEPROM.commit();
    LOG_Serial.println("Parameters set to default");
}

void eeprom_get() {
  EEPROM.get(1, parameters);
}

void eeprom_update() {
  if ((parameters.threshold_lvl != THRESHOLD_LVL_DEFAULT) |
      (parameters.steering_max_speed != STEERING_MAX_SPEED_DEFAULT) |
      (parameters.steering_speed_coef != STEERING_SPEED_COEF_DEFAULT) |
      (parameters.max_angle != MAX_ANGLE_DEFAULT) |
      (parameters.angle_coef != ANGLE_COEF_DEFAULT) |
      (parameters.min_servo_pulse != MIN_SERVO_PULSE_DEFAULT) |
      (parameters.max_servo_pulse != MAX_SERVO_PULSE_DEFAULT) |
      (parameters.lead_angle != LEAD_ANGLE_DEFAULT)) { 
        EEPROM.put(1, parameters);
        EEPROM.commit();
  }
}
