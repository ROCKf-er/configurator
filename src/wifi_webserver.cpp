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

String p_str = "";

extern mavlink_param_value_t param_arr[20];
extern param_constraint param_costraint_arr[20];


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


void build_set_buttons(WiFiClient client) {
  client.println("<button class=\"greenbutton\" onclick=\"upload_values();\">SET</button>");
  client.println("<button class=\"redbutton\" onclick=\"if( confirm('This will return all values to their default values. Are you sure?') ){location.href = '/default';};\">SET DEFAULT</button>");  
}


void build_header(WiFiClient client) {
  client.println("<!DOCTYPE html><html>");
  client.println("<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
  client.println("<link rel=\"icon\" href=\"data:,\">");
  client.println("<style>");
  client.println("html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}");
  client.println(".button { background-color: #4CAF50; border: none; color: white; padding: 5px 15px;");
  client.println("text-decoration: none; font-size: 25px; margin: 2px; cursor: pointer;}");
  client.println(".button2 {background-color: #555555;} table, th, td { border: 1px solid black; border-collapse: collapse; padding: 5px; text-align: left; } th { background-color: #D0D0D0; }");
  client.println(".redbutton { background-color: #D09090; padding: 5px 5px; margin: 10px;}");
  client.println(".greenbutton { background-color: #90D090; padding: 5px 50px; margin: 10px;}");
  client.println("input { width: 8em; }");
  client.println("input:invalid { border: 1px dashed red; background-color: pink; }");  
  client.println("</style></head>");
  client.println("<body>");
  build_set_buttons(client);
  client.println("<br>");
  //client.println("header");
  //client.println("<br>");
  //client.println(header);
  //client.println("<br>");
  //client.println(p_str);
}


void build_table_rows(WiFiClient client) {
  for (uint16_t i = 0; i < sizeof(param_arr) / sizeof(param_arr[0]); i++) {
    if (param_arr[i].param_id[0] == '\0') {
      break;
    }
    client.println("<tr>");
    client.printf("<td>%d</td>", param_arr[i].param_index);
    client.printf("<td>%s</td>", param_arr[i].param_id);
    // https://mavlink.io/en/messages/common.html#PARAM_VALUE
    // MAV_PARAM_TYPE
    // 1..8 - integer
    // 9..10 - floar
    if (param_arr[i].param_type <= 8) {
      client.printf("<td><input type=number value=%.0f min=%.0f max=%.0f step=%.0f uploadname=\"v%d\" /></td>", 
        param_arr[i].param_value, 
        param_costraint_arr[i].min_value, 
        param_costraint_arr[i].max_value, 
        param_costraint_arr[i].step_value,
        param_arr[i].param_index
      );
      client.printf("<td>%.0f</td>", param_costraint_arr[i].default_value);
      client.printf("<td>%.0f..%.0f</td>", param_costraint_arr[i].min_value, param_costraint_arr[i].max_value);    
    } else {    
      client.printf("<td><input type=number value=%.2f min=%.2f max=%.2f step=%.2f uploadname=\"v%d\" /></td>", 
        param_arr[i].param_value, 
        param_costraint_arr[i].min_value, 
        param_costraint_arr[i].max_value, 
        param_costraint_arr[i].step_value,
        param_arr[i].param_index
      );
      client.printf("<td>%.2f</td>", param_costraint_arr[i].default_value);
      client.printf("<td>%.2f..%.2f</td>", param_costraint_arr[i].min_value, param_costraint_arr[i].max_value);
    }
    client.printf("<td>%s</td>", param_costraint_arr[i].description);
    client.printf("</tr>");
  }     
}


void build_table(WiFiClient client) {
  client.println("<table>");
  client.println("<tr>");
  client.println("<th>Index</th>");
  client.println("<th>ID</th>");
  client.println("<th>Value</th>");
  client.println("<th>Default</th>");
  client.println("<th>Range</th>");
  client.println("<th>Description</th>");
  client.println("</tr>");

  build_table_rows(client);

  client.println("</table>");
}


void build_footer(WiFiClient client) {
  client.println("<br>");
  build_set_buttons(client);
  client.println("<br>");
  client.println("<script>");
  client.println("function upload_values() {var table = document.getElementsByTagName(\"table\")[0]; var inputs = document.getElementsByTagName(\"input\"); var params = \"/?\"; for (var i=0; i<inputs.length; i++) { var uploadname = inputs[i].getAttribute(\"uploadname\"); if (uploadname == null) { break; } if (i > 0) { params += \"&\"; } params += inputs[i].getAttribute(\"uploadname\") + \"=\" + inputs[i].value; } location.href = params; }");
  client.println("function docKeyup(){var table = document.getElementsByTagName(\"table\")[0];var inputs = document.getElementsByTagName(\"input\");var isAllValid = true;for (var i=0; i<inputs.length; i++) {if (!inputs[i].checkValidity()) {isAllValid = false;}}var buttons = document.getElementsByClassName(\"greenbutton\");for (var i=0; i<buttons.length; i++) {var b = buttons[i];b.disabled = !isAllValid;}}document.addEventListener(\"keyup\", docKeyup);document.onload = docKeyup();document.addEventListener(\"click\", docKeyup);");
  client.println("</script>");
  client.println("</body></html>");  
  /*
  client.println("<p></p>");           
  client.println("<p>LOG</p>");
  client.println("<p align = \"left\">");
  for(uint8_t i = 0; i < HTML_LOG_LENGTH; i++){
    client.println(html_log[i]);
    client.println("<br>");
  }
  client.println("</p>");
  client.println("</body></html>");            
  */

  // The HTTP response ends with another blank line
  client.println();
}


void build_page(WiFiClient client) {
  build_header(client);
  build_table(client);
  build_footer(client);
}


void get_value_from_pair_str(String pair) {
  int index_of_equal = pair.indexOf("=");
  String index_str = pair.substring(0, index_of_equal);
  int index = index_str.toInt();

  String val_str = pair.substring(index_of_equal + 1);
  float val = val_str.toFloat();
 // LOG_Serial.printf("String: %s, index = %d\n", pair, index);

  mav_param_set(index, val);
}


void get_values_from_str(String vs) {
  p_str = vs;

  int amp_index = vs.indexOf("&");
  while (amp_index > 0) {
    String pair = vs.substring(0, amp_index);
    get_value_from_pair_str(pair);
    vs = vs.substring(amp_index + 1);
    amp_index = vs.indexOf("&");
  }
  get_value_from_pair_str(vs);
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

            if (header.indexOf("GET /default") >= 0) {
              // reset to default
              eeprom_set_default();
            }                       

            if (header.indexOf("GET /?") >= 0) {
              int b_index = header.indexOf("GET /?") + 6;
              String vs = header.substring(b_index);
              int e_index = vs.indexOf(" ");
              vs = vs.substring(0, e_index);

              get_values_from_str(vs);
            }

            build_page(client);

            client.stop();

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







