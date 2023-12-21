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

extern mavlink_param_value_t param_arr[PARAM_COUNT];
extern param_constraint param_costraint_arr[PARAM_COUNT];
extern char statustext_displayed[50];

void wifi_init()
{
  Serial.println("");
  Serial.println("Setting AP (Access Point)… ");

  char ssid[30];
  snprintf(ssid, 30, SSID_PREFIX, board_ID); // SSID + board ID
  WiFi.softAP(ssid, PASSWORD);

  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP SSID = ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(IP);

  server.begin();
}

void build_set_buttons(WiFiClient client)
{
  client.println("<button class=\"yellowbutton\" onclick=\"{location.href = '/';}\">GET</button>");
  client.println("<button class=\"greenbutton\" onclick=\"upload_values();\">SET</button>");
  client.println("<button class=\"redbutton\" onclick=\"if( confirm('This will return all values to their default values. Are you sure?') ){location.href = '/default';};\">SET DEFAULT</button>");
  char statustext_char[11];
  strncpy(statustext_char, statustext_displayed, 10);
  statustext_char[10] = '\0';
  if (get_status_saved())
  {
    client.printf("<label id=\"statelabel\" class=\"labelgreen\">%s</label>", statustext_char);
  }
  else
  {
    client.printf("<label id=\"statelabel\" class=\"labelorange\">%s</label>", statustext_char);
  }
}

void build_header(WiFiClient client)
{
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
  client.println(".yellowbutton { background-color: #D0D090; padding: 5px 50px; margin: 10px;}");
  client.println(".labelorange{color: #e0a100;}.labelgreen{color: #02a82e;}");
  client.println("input[type=number] { width: 8em; }");
  client.println("input:invalid { border: 1px dashed red; background-color: pink; }");
  client.println("#bitmaskdiv { display: none; background-color: #EBEBEB; position: absolute; top: 50%; left: 50%; padding: 10px; transform: translate(-50\%,-50\%);}");
  client.println("#openingbuttondiv { display: none; background-color: #CBEBEB; position: absolute; top: 50%; left: 50%; }");
  //client.println("input[type=\"checkbox\"]{ display: inline-block; vertical-align: middle; cursor: pointer;}");
  //client.println(".checkboxlabel {display: flex; align-items: center; padding: 2px;}");
  client.println(".bitmaptable { margin-top: 10px; }");  
  client.println(".editbutton { background-color: #90D090; }");
  client.println("</style></head>");
  client.println("<body>");
  build_set_buttons(client);
  client.println("<br>");
}

void build_table_rows(WiFiClient client)
{
  for (uint16_t i = 0; i < sizeof(param_arr) / sizeof(param_arr[0]); i++)
  {
    if (param_arr[i].param_id[0] == '\0')
    {
      break;
    }
    client.println("<tr>");
    client.printf("<td>%d</td>", param_arr[i].param_index);

    char param_id[17];
    if (param_costraint_arr[i].actual)
    {
      strncpy(param_id, param_arr[i].param_id, 16);
    }
    else
    {
      strncpy(param_id, "################", 16);
    }
    param_id[16] = '\0';
    client.printf("<td>%s</td>", param_id);

    // https://mavlink.io/en/messages/common.html#PARAM_VALUE
    // MAV_PARAM_TYPE
    // 1..8 - integer
    // 9..10 - floar
    if (param_arr[i].param_type <= 8)
    {
      client.printf("<td><input type=number value=%.0f min=%.0f max=%.0f step=%.0f uploadname=\"v%d\" bitmask=\"%s\" /></td>",
                    param_arr[i].param_value,
                    param_costraint_arr[i].min_value,
                    param_costraint_arr[i].max_value,
                    param_costraint_arr[i].step_value,
                    param_arr[i].param_index,
                    param_costraint_arr[i].bitmask);
      client.printf("<td>%.0f</td>", param_costraint_arr[i].default_value);
      client.printf("<td>%.0f..%.0f</td>", param_costraint_arr[i].min_value, param_costraint_arr[i].max_value);
    }
    else
    {
      client.printf("<td><input type=number value=%.2f min=%.2f max=%.2f step=%.2f uploadname=\"v%d\" bitmask=\"\" /></td>",
                    param_arr[i].param_value,
                    param_costraint_arr[i].min_value,
                    param_costraint_arr[i].max_value,
                    param_costraint_arr[i].step_value,
                    param_arr[i].param_index);
      client.printf("<td>%.2f</td>", param_costraint_arr[i].default_value);
      client.printf("<td>%.2f..%.2f</td>", param_costraint_arr[i].min_value, param_costraint_arr[i].max_value);
    }
    client.printf("<td>%s</td>", param_costraint_arr[i].description);
    client.printf("</tr>");
  }
}

void build_table(WiFiClient client)
{
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

void build_footer(WiFiClient client, bool need_reload)
{
  client.println("<br>");
  build_set_buttons(client);
  client.println("<br>");
  client.println("<div id=\"openingbuttondiv\">");
  client.println("<input type=\"button\" value=\"Edit Bits\" onclick=\"editbitsclick()\" class=\"editbutton\"/>");
  client.println("</div>");
  client.println("<div id=\"bitmaskdiv\"> </div>");
  client.println("<script src=\"javascript.js\"></script>");
  client.println("<script src=\"bitmask.js\"></script>");

  if (need_reload) {
    client.println("<script>");
    client.println("if(window.addEventListener){");
    client.println("window.addEventListener('load', reload_with_delay)");
    client.println("}else{");
    client.println("window.attachEvent('onload', reload_with_delay)");
    client.println("}");
    client.println("function reload_with_delay() {");
    client.println("setTimeout(() => { location.href = \"/\"; }, 5500);");
    client.println("}");
    client.println("</script>");
  }

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

void build_page(WiFiClient client, bool need_reload)
{
  update_parameters();

  build_header(client);
  build_table(client);
  build_footer(client, need_reload);
}

void build_script(WiFiClient client)
{
  client.println("function upload_values() {");
  client.println("var table = document.getElementsByTagName(\"table\")[0];");
  client.println("var inputs = document.getElementsByTagName(\"input\");");
  client.println("var params = \"/?\";");
  client.println("for (var i=0; i<inputs.length; i++) {");
  client.println("var uploadname = inputs[i].getAttribute(\"uploadname\");");
  client.println("if (uploadname == null) {");
  client.println("break;");
  client.println("}");
  client.println("if (i > 0) {");
  client.println("params += \"&\";");
  client.println("}");
  client.println("params += inputs[i].getAttribute(\"uploadname\") + \"=\" + inputs[i].value;");
  client.println("}");
  client.println("location.href = params;");
  client.println("}");
  client.println("function docKeyup(){");
  client.println("var table = document.getElementsByTagName(\"table\")[0];");
  client.println("var inputs = document.getElementsByTagName(\"input\");");
  client.println("var isAllValid = true;");
  client.println("for (var i=0; i<inputs.length; i++) {");
  client.println("if (!inputs[i].checkValidity()) {");
  client.println("isAllValid = false;");
  client.println("}");
  client.println("}");
  client.println("var buttons = document.getElementsByClassName(\"greenbutton\");");
  client.println("for (var i=0; i<buttons.length; i++) {");
  client.println("var b = buttons[i];");
  client.println("b.disabled = !isAllValid;");
  client.println("}");
  client.println("}");
  client.println("document.addEventListener(\"keyup\", docKeyup);");  
  client.println("if(window.addEventListener){");
  client.println("window.addEventListener('load', docKeyup)");
  client.println("}else{");
  client.println("window.attachEvent('onload', docKeyup)");
  client.println("}");
  client.println("document.addEventListener(\"click\", docKeyup);");
}

void build_script_bitmask(WiFiClient client)
{
  client.println("var bitmaskdiv;");
  client.println("var openingbuttondiv;");
  client.println("var bitmask = \"\";");
  client.println("var edited_input;");
  client.println("if(window.addEventListener){");
  client.println("window.addEventListener('load', init)");
  client.println("}else{");
  client.println("window.attachEvent('onload', init)");
  client.println("}");
  client.println("function init() {");
  client.println("bitmaskdiv = document.getElementById(\"bitmaskdiv\");");
  client.println("bitmaskdiv_showing(false);");
  client.println("bitmaskdiv.addEventListener(\"focusout\", bitmaskdivfocusout);");
  client.println("openingbuttondiv = document.getElementById(\"openingbuttondiv\");");
  client.println("openingbuttondiv_showing(false);");
  client.println("window.addEventListener(\"click\", function() {");
  client.println("openingbuttondiv_showing(false);");
  client.println("bitmaskdiv_showing(false);");
  client.println("});");
  client.println("bitmaskdiv.addEventListener(\"click\", function() {");
  client.println("var event = arguments[0] || window.event;");
  client.println("event.stopPropagation();");
  client.println("});");
  client.println("var inputs = document.getElementsByTagName(\"input\");");
  client.println("for (var i=0; i<inputs.length; i++) {");
  client.println("var input = inputs[i]");
  client.println("var uploadname = input.getAttribute(\"uploadname\");");
  client.println("if (uploadname != null) {");
  client.println("input.addEventListener(\"focus\", inputfocus);");
  client.println("input.addEventListener(\"focusout\", inputfocusout);");
  client.println("input.addEventListener(\"click\", function() {");
  client.println("var event = arguments[0] || window.event;");
  client.println("event.stopPropagation();");
  client.println("edited_input = this;");
  client.println("});");
  client.println("input.addEventListener(\"mouseup\", function() {");
  client.println("edited_input = this;");
  client.println("});");
  client.println("}");
  client.println("}");
  client.println("}");
  client.println("function inputfocus(e) {");
  client.println("bitmaskdiv_showing(false);");
  client.println("edited_input = e.target;");
  client.println("bitmask = e.target.getAttribute(\"bitmask\");");
  client.println("if (bitmask != null && bitmask != \"\") {");
  client.println("openingbuttondiv_showing(true);");
  client.println("} else {");
  client.println("openingbuttondiv_showing(false);");
  client.println("}");
  client.println("var rect = e.target.getBoundingClientRect();");
  client.println("var scrolltop = window.scrollX || document.documentElement.scrollTop || document.body.scrollTop;");
  client.println("button_top = rect.top + scrolltop;");
  client.println("button_left = rect.right + 10;");
  client.println("//openingbuttondiv.style.position = 'absolute';");
  client.println("openingbuttondiv.style.top = '' + button_top + 'px';");
  client.println("openingbuttondiv.style.left = '' + button_left + 'px';");
  client.println("}");
  client.println("function inputfocusout(e) {");
  client.println("return;");
  client.println("openingbuttondiv_showing(false);");
  client.println("}");
  client.println("function editbitsclick(e) {");
  client.println("var event = arguments[0] || window.event;");
  client.println("event.stopPropagation();");
  client.println("openingbuttondiv_showing(false);");
  client.println("bitmaskdiv_showing(true);");
  client.println("}");
  client.println("function bitmaskdivfocusout(e) {");
  client.println("}");
  client.println("function bitmaskdiv_showing(is_show) {");
  client.println("//bitmaskdiv.style.position = 'absolute';");
  client.println("if (is_show) {");
  client.println("var scrolltop = window.scrollX || document.documentElement.scrollTop || document.body.scrollTop;");
  client.println("var top = window.innerHeight / 2 + scrolltop;");
  client.println("bitmaskdiv.style.top = '' + top + 'px'");
  client.println("bitmaskdiv.style.display = 'inline-block';");
  client.println("buil_bitmaskdiv();");
  client.println("} else {");
  client.println("bitmaskdiv.style.display = 'none';");
  client.println("}");
  client.println("}");
  client.println("function openingbuttondiv_showing(is_show) {");
  client.println("if (is_show) {");
  client.println("openingbuttondiv.style.display = 'inline-block';");
  client.println("} else {");
  client.println("openingbuttondiv.style.display = 'none';");
  client.println("}");
  client.println("}");
  client.println("function dec2bin(dec) {");
  client.println("return (dec >>> 0).toString(2);");
  client.println("}");
  client.println("function buil_bitmaskdiv() {");
  client.println("console.log(bitmask);");
  client.println("bitmask_arr = bitmask.split(\", \");");
  client.println("console.log(bitmask_arr);");
  client.println("var bit_str = dec2bin(0 + edited_input.value);");
  client.println("console.log(bit_str);");
  client.println("bitmaskdiv.innerHTML = \"\";");  
  client.println("var value_label = document.createElement('label');");
  client.println("value_label.id = \"value_label\";");
  client.println("value_label.innerHTML = edited_input.value;");
  client.println("bitmaskdiv.appendChild(value_label);");
  client.println("bitmaskdiv.innerHTML += '<br/>';");
  client.println("bitmasktable = document.createElement('table');");
  client.println("bitmaskdiv.appendChild(bitmasktable);");
  client.println("bitmasktable.setAttribute(\"class\", \"bitmaptable\");");
  client.println("for (var n=0; n<bitmask_arr.length; n++) {");
  client.println("bitmaskrow = document.createElement('tr');");
  client.println("bitmasktable.appendChild(bitmaskrow);");
  client.println("bitmaskcell = document.createElement('td');");
  client.println("bitmaskrow.appendChild(bitmaskcell);");
  client.println("var bit = 0 + bit_str[bit_str.length - 1 - n]");
  client.println("var checkbox = document.createElement('input');");
  client.println("checkbox.type = 'checkbox';");
  client.println("checkbox.id = 'checkbox_' + n;");
  client.println("checkbox.name = 'checkbox_' + n;");
  client.println("checkbox.class = 'bitcheckbox';");
  client.println("checkbox.setAttribute(\"onclick\", \"checkbox_cliced()\");");
  client.println("checkbox.setAttribute(\"w_value\", '' + 1<<n);");
  client.println("bitmaskcell.appendChild(checkbox);");
  client.println("if (bit > 0) {");
  client.println("checkbox.setAttribute('checked', 'checked');");
  client.println("}");
  client.println("var checkbox_label = document.createElement('label');");
  client.println("checkbox_label.for = 'checkbox_' + n;");
  client.println("checkbox_label.setAttribute(\"class\", \"checkboxlabel\");");
  client.println("checkbox_label.innerHTML = bitmask_arr[n];");
  client.println("bitmaskcell.appendChild(checkbox_label);");
  client.println("}");
  client.println("}");
  client.println("function checkbox_cliced() {");
  client.println("var s = 0;");
  client.println("var value_label = document.getElementById(\"value_label\");");
  client.println("var checkboxes = document.getElementsByTagName(\"input\");");   
  client.println("for (var i=0; i<checkboxes.length; i++) {");
  client.println("if (checkboxes[i].hasAttribute(\"w_value\")) {");
  client.println("var w_value = +checkboxes[i].getAttribute(\"w_value\");");
  client.println("if (checkboxes[i].checked) {");
  client.println("s += w_value;");
  client.println("}");
  client.println("}");
  client.println("}");
  client.println("value_label.innerHTML = '' + s;");
  client.println("edited_input.value = '' + s;");
  client.println("}");
}

void get_value_from_pair_str(String pair)
{
  int index_of_equal = pair.indexOf("=");
  String index_str = pair.substring(1, index_of_equal);
  int index = index_str.toInt();

  String val_str = pair.substring(index_of_equal + 1);
  float val = val_str.toFloat();

  if (!equal(val, param_arr[index].param_value))
  {
    mav_param_set(index, val);

    reset_status_saved();
  }
}

void get_values_from_str(String vs)
{
  p_str = vs;

  int amp_index = vs.indexOf("&");
  while (amp_index > 0)
  {
    String pair = vs.substring(0, amp_index);
    get_value_from_pair_str(pair);
    vs = vs.substring(amp_index + 1);
    amp_index = vs.indexOf("&");
  }
  get_value_from_pair_str(vs);
}

void set_default()
{
  for (uint16_t i = 0; i < PARAM_COUNT; i++)
  {
    mav_param_set(i, param_costraint_arr[i].default_value);
  }
}

void wifi_work()
{
  WiFiClient client = server.available(); // Listen for incoming clients

  if (client)
  {                          // If a new client connects,
    String currentLine = ""; // make a String to hold incoming data from the client
    while (client.connected())
    { // loop while the client's connected
      if (client.available())
      {                         // if there's bytes to read from the client,
        char c = client.read(); // read a byte, then
        // Serial.write(c);                    // print it out the serial monitor
        header += c;
        if (c == '\n')
        { // if the byte is a newline character
          if (currentLine.length() == 0)
          {
            if (header.indexOf("GET /javascript.js") >= 0)
            {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-type:application/javascript");
              client.println("Connection: close");
              client.println();
              build_script(client);
            }
            else if (header.indexOf("GET /bitmask.js") >= 0)
            {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-type:application/javascript");
              client.println("Connection: close");
              client.println();
              build_script_bitmask(client);
            }
            else
            {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-type:text/html");
              client.println("Connection: close");
              client.println();

              String get_string = "GET /par_";
              int8_t pos = header.indexOf(get_string);

              if (header.indexOf("GET /default") >= 0)
              {
                // reset to default
                // eeprom_set_default();
                set_default();
              }

              bool need_reload = false;
              if (header.indexOf("GET /?") >= 0)
              {
                need_reload = true;
                int b_index = header.indexOf("GET /?") + 6;
                String vs = header.substring(b_index);
                int e_index = vs.indexOf(" ");
                vs = vs.substring(0, e_index);

                get_values_from_str(vs);
              }

              build_page(client, need_reload);
            }

            client.stop();

            header = "";

            // Break out of the while loop
            break;
          }
          else
          { // if you got a newline, then clear currentLine
            currentLine = "";
          }
        }
        else if (c != '\r')
        {                   // if you got anything else but a carriage return character,
          currentLine += c; // add it to the end of the currentLine
        }
      }
      else
      {
        // Close the connection
        client.stop();
        // Clear the header variable
        header = "";
      }
    }
  }
}

void html_log_clear()
{
  for (uint8_t i = 0; i < HTML_LOG_LENGTH; i++)
  {
    html_log[i] = "";
  }
}

void html_log_write(const String &string, uint8_t position)
{
  if ((position >= 0) && (position < HTML_LOG_LENGTH))
  {
    html_log[position] = string;
  }
}

void html_log_add(String string)
{
  static uint8_t position = 0;
  String temp_string;

  if (position < HTML_LOG_LENGTH)
  {
    html_log_write(string, position);
    position++;
  }
  else
  {
    html_log_clear();
    position = 0;
    html_log_write(string, position);
  }
}

void param_change(float &param, char sign, float step, float min, float max)
{
  switch (sign)
  {
  case '-':
    param = constrain(param - step, min, max);
    break;
  case '+':
    param = constrain(param + step, min, max);
    break;
  default:
    break;
  }
}

void param_change(uint16_t &param, char sign, uint16_t step, uint16_t min, uint16_t max)
{
  switch (sign)
  {
  case '-':
    param = constrain(param - step, min, max);
    break;
  case '+':
    param = constrain(param + step, min, max);
    break;
  default:
    break;
  }
}

void param_change(int16_t &param, char sign, int16_t step, int16_t min, int16_t max)
{
  switch (sign)
  {
  case '-':
    param = constrain(param - step, min, max);
    break;
  case '+':
    param = constrain(param + step, min, max);
    break;
  default:
    break;
  }
}
