#ifndef _EEPROM_H
#define _EEPROM_H

#define EEPROM_UPDATE_PERIOD_MS     1000
#define INIT_KEY                    125
#define THRESHOLD_LVL_DEFAULT       90
#define MAV_MSG_RATE_MS_DEFAULT     500
#define STEERING_MAX_SPEED_DEFAULT  (5.0f)
#define STEERING_SPEED_COEF_DEFAULT (0.05f)
#define MAX_ANGLE_DEFAULT           (20.0f)
#define ANGLE_COEF_DEFAULT          (1.0f)
#define MIN_SERVO_PULSE_DEFAULT     600
#define MAX_SERVO_PULSE_DEFAULT     2400
#define LEAD_ANGLE_DEFAULT          5
#define EEPROM_SIZE                 (sizeof(parameters) + 1) // struct Parameters + init key

void eeprom_init();
void eeprom_set_default();
void eeprom_get();
void eeprom_update();

#endif //_EEPROM_H