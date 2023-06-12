#ifndef FILTER_H
#define FILTER_H

#include <stdint.h>

void write_filtered_data(uint8_t &target, uint8_t source, float f_coef);
void write_filtered_data(int16_t &target, int16_t source, float f_coef);

#endif