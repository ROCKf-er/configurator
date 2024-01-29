#ifndef PID_H
#define PID_H

class PID {
private: 
    float I;
    float dErr;
    float time;
    float time_old;
    float dt; // discr period
    float error;
    float error_old; 
public:
    float Kp;
    float Ki;
    float Kd;
    float U_target;
    float U;
    float out;

    PID();
    void clear();
    void setCoef(float p, float i, float d);
    float get(float curr_value, float target_value);
};

#endif //PID_H