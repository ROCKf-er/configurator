#ifndef DATA_DISPLAY_H
#define DATA_DISPLAY_H
    #include "TFT_eSPI.h"
    #include "main.h"

    #define DISP_HEIGHT 135
    #define DISP_WIDTH  240

    #define TEXT_SIZE 2
    #define MAX_LVL 130

    void set_log_text(data_r &data_radar_structure);
    void view_alarm();
    void view_sig_level(uint8_t signal_lvl);
    void testdrawcircle(uint8_t signal_lvl, int16_t x, int16_t y);
    void clear_println(int num, int16_t x, int16_t y);
    void display_clear();
    void printID();    
    void print_text(String str, uint8_t x, uint8_t y);

#endif //DATA_DISPLAY_H