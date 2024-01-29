#include <Arduino.h>
#include "PID.h"

PID::PID(){
    clear();
    setCoef(0.0, 0.0, 0.0);
}

void PID::clear(){
    I = 0.0;
    dErr = 0.0;
    error_old = 0.0;
    time_old = millis();
}

void PID::setCoef(float p, float i, float d){
    Kp = (p < 0)? 0 : p;    
    Ki = (i < 0)? 0 : i;    
    Kd = (i < 0)? 0 : i;    
    clear();
}

float PID::get(float curr_value, float target_value) {
    time = millis();
    dt = (time - time_old) / 1000;
    if (dt < 1) {
        error = target_value - curr_value;
        I += error;
        dErr = error - error_old;
        out =  Kp * (error + Ki * I * dt + Kd * dErr / dt);
        error_old = error;
        time_old = time;
        return out;
    } else {
        clear();
        return 0;
    }
}
  