#ifndef WIFI_WEBSERVER_H
#define WIFI_WEBSERVER_H

#define SSID_PREFIX        "Seekroy_%04x"
#define PASSWORD           "87654321"

#define WEBSERVER_PORT_NUM 80

#define HTML_LOG_LENGTH 100


void wifi_init();
void wifi_work();
void html_log_clear();
void html_log_write(const String &string, uint8_t position);
void html_log_add(String string);
void param_change(float &param, char sign, float step, float min, float max);
void param_change(uint16_t &param, char sign, uint16_t step, uint16_t min, uint16_t max);
void param_change(int16_t &param, char sign, int16_t step, int16_t min, int16_t max);



#endif //WIFI_WEBSERVER_H