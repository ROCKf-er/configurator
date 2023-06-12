#include "filter.h"

void write_filtered_data(uint8_t &target, uint8_t source, float f_coef){
  // f_coef = 0 - filter off
  // f_coef = 0.99 - max filtering

  target = target * f_coef + source * (1 - f_coef);
}

void write_filtered_data(int16_t &target, int16_t source, float f_coef){
  // f_coef = 0 - filter off
  // f_coef = 0.99 - max filtering

  target = target * f_coef + source * (1 - f_coef);
} 