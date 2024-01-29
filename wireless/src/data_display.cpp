#include "data_display.h"
#include "main.h"


uint8_t buff[10];
extern TFT_eSPI display;
extern uint32_t board_ID;
extern Parameters parameters;

/*
void set_log_text(data_r &data_radar_structure)
{
  
  display.setTextSize(TEXT_SIZE); // Draw 2X-scale text
  display.setTextColor(TFT_WHITE, TFT_BLACK);

  clear_println(data_radar_structure.xm, 1, 1 * TEXT_SIZE);
  clear_println(data_radar_structure.xp, 1, 10 * TEXT_SIZE);
  clear_println(data_radar_structure.ym, 1, 20 * TEXT_SIZE);
  clear_println(data_radar_structure.yp, 1, 30 * TEXT_SIZE);
  clear_println(data_radar_structure.angle_x, 1, 40 * TEXT_SIZE);
  clear_println(data_radar_structure.angle_y, 1, 50 * TEXT_SIZE);

  clear_println(data_radar_structure.level, 40 * TEXT_SIZE, 60 * TEXT_SIZE);
}
*/


void view_alarm()
{
  display.setTextSize(4); // Draw 2X-scale text
  display.setTextColor(TFT_WHITE);
  display.setCursor(5, 5);
  display.println("NO DATA");
}


void view_sig_level(uint8_t signal_lvl)
{
  uint32_t bar_color;
  uint8_t normalized_level;

  if (signal_lvl > MAX_LVL) {
    signal_lvl = MAX_LVL;
    bar_color = TFT_RED;
  } else {
    bar_color = TFT_WHITE;
  }

  normalized_level = signal_lvl / (MAX_LVL / (float)display.height());

  display.fillRect(60, 0, 8, display.height(), TFT_DARKGREY);
  display.fillRect(60, display.height() - normalized_level, 8, display.height(), bar_color);
}


void clear_println(int num, int16_t x, int16_t y){
  const uint8_t col_width = 4;  // max 4 digits/chars  =  digits + spaces     
  uint8_t digits;               // num of digits
  uint8_t spaces;               // num of spaces after digits 

  display.setCursor(x, y);
  digits = display.print(num);

  if (digits <= col_width) {
    spaces = col_width - digits;
  } else {
    spaces = col_width;
  }

  for (spaces; spaces != 0; spaces--){  //fill in spaces
    display.print(" ");
  }
  display.println();
} 

void display_clear(){
  display.fillScreen(TFT_BLACK);
}   

void printID(){
  display_clear();
  display.setTextSize(2); 
  display.setTextColor(TFT_WHITE);
  display.setCursor(5, 5);
  display.printf("ID = %4x", board_ID);
  delay(1000);
  display_clear();
}
void print_text(String str, uint8_t x, uint8_t y){
  display_clear();
  display.setTextSize(2); 
  display.setTextColor(TFT_WHITE);
  display.setCursor(x, y);
  display.print(str);
}


