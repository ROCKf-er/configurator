#include <WiFi.h>
#include "wifi_webserver.h"
#include <string>
#include "main.h"
#include "_eeprom.h"
#include <ESP32Servo.h>
#include <common/mavlink.h>

WiFiServer server(WEBSERVER_PORT_NUM);
uint32_t board_ID = ESP.getEfuseMac() >> 32;
String html_log[HTML_LOG_LENGTH];
String header;

extern mavlink_param_value_t param_arr[20];

void wifi_init() {
  Serial.println("");
  Serial.println("Setting AP (Access Point)… ");
 
  char ssid[30];
  snprintf(ssid, 30, SSID_PREFIX, board_ID);        // SSID + board ID
  WiFi.softAP(ssid, PASSWORD);

  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP SSID = ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(IP);
  
  server.begin();
}

void wifi_work(){
  WiFiClient client = server.available();   // Listen for incoming clients

  

  if (client) {                             // If a new client connects,
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        //Serial.write(c);                    // print it out the serial monitor
        header += c;
        if (c == '\n') {                    // if the byte is a newline character
          if (currentLine.length() == 0) {
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println("Connection: close");
            client.println();
            
            String get_string = "GET /par_";
            int8_t pos = header.indexOf(get_string);

            if (header.indexOf("GET /default") >= 0) {eeprom_set_default();}           // reset to default
            //if (header.indexOf("GET /noGPS") >= 0) {vehicle_mode = MODE_GUIDED_NOGPS;}  // Forced switch to Guided noGPS mode for debug
            //if (header.indexOf("GET /GPS") >= 0) {vehicle_mode = MODE_GUIDED_GPS;}      // Forced switch to Guided noGPS mode for debug
            
/*
            if (pos >= 0) {
              char par_number = header[pos + get_string.length()];      // parameter number to change 0..9
              char oper =       header[pos + get_string.length() + 2];  // Operator '+' or '-'

              switch (par_number) {
                case '0': 
                  param_change(param[0]->value, oper, 5, 10, 250);
                  Serial.printf("threshold_lvl changed to %.d\n", parameters.threshold_lvl);
                  break;  
                case '1': 
                  param_change(parameters.mav_msg_rate_ms, oper, 100, 100, 2000);
                  Serial.printf("mav_msg_rate_ms changed to %.d\n", parameters.mav_msg_rate_ms);
                  break;  
                case '2':
                  param_change(parameters.steering_max_speed, oper, 0.1, 0.1, 10);
                  Serial.printf("steering_max_speed changed to %.2f\n", parameters.steering_max_speed);
                  break;  
                case '3': 
                  param_change(parameters.steering_speed_coef, oper, 0.001, 0.001, 0.1);
                  Serial.printf("steering_speed_coef changed to %.3f\n", parameters.steering_speed_coef);
                  break;  
                case '4':   
                  param_change(parameters.max_angle, oper, 1.0, 1.0, 20.0);                
                  Serial.printf("max_angle changed to %.1f\n", parameters.max_angle);
                  break;  
                case '5': 
                  param_change(parameters.angle_coef, oper, 0.05, 0.0, 1.0);
                  Serial.printf("angle_coef_kp changed to %.2f\n", parameters.angle_coef);
                  break;  
                case '6': 
                  param_change(parameters.min_servo_pulse, oper, 50, 100, parameters.max_servo_pulse);
                  html_log_add("Reboot!");
                  Serial.printf("min_servo_pulse changed to %d\n", parameters.min_servo_pulse);
                  break;  
                case '7': 
                  param_change(parameters.max_servo_pulse, oper, 50, parameters.min_servo_pulse, 5000);
                  html_log_add("Reboot!");
                  Serial.printf("max_servo_pulse changed to %d\n", parameters.max_servo_pulse);
                  break;   
                case '8': 
                  param_change(parameters.lead_angle, oper, 5.0, -60, 60);
                  Serial.printf("lead_angle changed to %d\n", parameters.lead_angle);
                  break; 
                case '9': 
                  if (oper == '+') {
                    servo.writeMicroseconds(SERVO_MAX_PULSE);
                    LOG_Serial.println("OPEN");
                  } else {
                    servo.writeMicroseconds(SERVO_MIN_PULSE);
                    LOG_Serial.println("CLOSE");
                  }
                  break; 
                default: break; 
              }  
            }
  */
            
            
            // Display the HTML web page
            client.println("<!DOCTYPE html><html>");
            client.println("<head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
            client.println("<link rel=\"icon\" href=\"data:,\">");
            // CSS to style the on/off buttons 
            // Feel free to change the background-color and font-size attributes to fit your preferences
            client.println("<style>html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}");
            client.println(".button { background-color: #4CAF50; border: none; color: white; padding: 5px 15px;");
            client.println("text-decoration: none; font-size: 25px; margin: 2px; cursor: pointer;}");
            client.println(".button2 {background-color: #555555;}</style></head>");
            
            // Web Page Heading
           // client.println("<body><a href=\"/\"><h3>Pelengator Web Server</h3></a>");

            client.println("<a href=\"/default\"> DEFAULT </a>");

            // Param adjusting   

            for (uint16_t i = 0; i < sizeof(param_arr) / sizeof(param_arr[0]); i++) {
              client.printf("<p align=\"right\">%d: %s: %.2f", param_arr[i].param_index, param_arr[i].param_id, param_arr[i].param_value);
              client.println("<a href=\"/par_0/-\"><button class=\"button\"> - </button></a>");
              client.println("<a href=\"/par_0/+\"><button class=\"button\"> + </button></a></p>");
            }


            client.println("<p></p>");
           
            client.println("<p>LOG</p>");
            client.println("<p align = \"left\">");
              for(uint8_t i = 0; i < HTML_LOG_LENGTH; i++){
                client.println(html_log[i]);
                client.println("<br>");
              }
            client.println("</p>");

      

            client.println("</body></html>");
            
            // The HTTP response ends with another blank line
            client.println();
            // Break out of the while loop
            break;
          } else { // if you got a newline, then clear currentLine
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      } else {
        // Close the connection
        client.stop();
        // Clear the header variable
        header = "";
        Serial.println("");
      }

    }
  }
}

void html_log_clear(){
  for(uint8_t i = 0; i < HTML_LOG_LENGTH; i++){
    html_log[i] = "";
  }
}

void html_log_write(const String &string, uint8_t position){
  if ((position >= 0) && (position < HTML_LOG_LENGTH)){
    html_log[position] = string;
  }
}

void html_log_add(String string){
  static uint8_t position = 0;
  String temp_string;

  if (position < HTML_LOG_LENGTH) {
    html_log_write(string, position);
    position++;
  } else {
    html_log_clear();
    position = 0;
    html_log_write(string, position);
  }
}

void param_change(float &param, char sign, float step, float min, float max){
  switch (sign) {
    case '-': param = constrain(param - step, min, max); break;
    case '+': param = constrain(param + step, min, max); break;
    default: break;
  }
}

void param_change(uint16_t &param, char sign, uint16_t step, uint16_t min, uint16_t max){
  switch (sign) {
    case '-': param = constrain(param - step, min, max); break;
    case '+': param = constrain(param + step, min, max); break;
    default: break;
  }
}

void param_change(int16_t &param, char sign, int16_t step, int16_t min, int16_t max){
  switch (sign) {
    case '-': param = constrain(param - step, min, max); break;
    case '+': param = constrain(param + step, min, max); break;
    default: break;
  }
}







