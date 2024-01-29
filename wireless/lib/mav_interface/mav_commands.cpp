#include "mav_commands.h"

#include "mavlink.h"
#include "common.h"
#include "ardupilotmega.h"

#define TYPE_MASK_USE_POSITION 0x0DF8
#define TYPE_MASK_USE_VELOCITY 0x0DC7
#define TYPE_MASK_USE_ACCELERATION 0x0C3F
#define TYPE_MASK_USE_POS_VEL 0x0DC0
#define TYPE_MASK_USE_POS_VEL_ACCEL 0x0C00
#define TYPE_MASK_USE_YAW 0x09FF
#define TYPE_MASK_USE_YAW_RATE 0x05FF

#define LAT_LON_SCALE 10000000


/**
 * @brief Get mavlink message to enter guided mode
 *
 */
void mav_get_msg_set_guided(unsigned char *res_buf, unsigned int *len, bool enable)
{
    // Prepare command for off-board mode
    mavlink_set_mode_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.base_mode = (enable ? MAV_MODE_GUIDED_ARMED : MAV_MODE_AUTO_ARMED) |
                    MAV_MODE_FLAG_CUSTOM_MODE_ENABLED;
    com.custom_mode = enable ? COPTER_MODE_GUIDED : COPTER_MODE_AUTO;

    // Encode
    mavlink_message_t message;
    mavlink_msg_set_mode_encode(SYSTEM_ID, COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}

/**
 * @brief Get command to move to the specified position
 * Positions are relative to the vehicle’s EKF Origin in NED frame
 * I.e x=1,y=2,z=3 is 1m North, 2m East and 3m Down from the origin
 * The EKF origin is the vehicle’s location when it first achieved a good position estimate
 * Velocity and Acceleration are in NED frame
 *
 * @param x_m X Position in meters (positive is North)
 * @param y_m Y Position in meters (positive is East)
 * @param z_m Z Position in meters (positive is down)
 */
void mav_get_msg_ned_position_ekf(unsigned char *res_buf, unsigned int *len, float x_m, float y_m, float z_m)
{
    mavlink_set_position_target_local_ned_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.target_component = MAV_DEFAULT_TARG_COMPONENT;
    com.coordinate_frame = MAV_FRAME_LOCAL_NED;
    com.type_mask = TYPE_MASK_USE_POSITION;
    com.x = x_m;
    com.y = y_m;
    com.z = z_m;
    // Encode
    mavlink_message_t message;
    mavlink_msg_set_position_target_local_ned_encode(SYSTEM_ID, COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}
/**
 * @brief Get command to move to the specified position
 * Positions are relative to the vehicle’s current position
 * I.e. x=1,y=2,z=3 is 1m North, 2m East and 3m below the current position.
 * Velocity and Acceleration are in NED frame
 *
 * @param x_m X Position in meters (positive is North)
 * @param y_m Y Position in meters (positive is East)
 * @param z_m Z Position in meters (positive is down)
 */
void mav_get_msg_ned_position_local_offset(unsigned char *res_buf, unsigned int *len, float x_m, float y_m, float z_m)
{
    mavlink_set_position_target_local_ned_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.target_component = MAV_DEFAULT_TARG_COMPONENT;
    com.coordinate_frame = MAV_FRAME_LOCAL_OFFSET_NED;
    com.type_mask = TYPE_MASK_USE_POSITION;
    com.x = x_m;
    com.y = y_m;
    com.z = z_m;
    // Encode
    mavlink_message_t message;
    mavlink_msg_set_position_target_local_ned_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}

/**
 * @brief Get command to move to the specified position
 * Positions are relative to the vehicle’s current position and heading
 * I.e x=1,y=2,z=3 is 1m forward, 2m right and 3m Down from the current position
 * Velocity and Acceleration are relative to the current vehicle heading.
 * Use this to specify the speed forward, right and down (or the opposite if you use negative values).
 * Specify yaw rate of zero to stop vehicle yaw from changing
 *
 * @param x_m X Position in meters (positive is forward)
 * @param y_m Y Position in meters (positive is right)
 * @param z_m Z Position in meters (positive is down)
 */
void mav_get_msg_ned_position_body_offset(unsigned char *res_buf, unsigned int *len, float x_m, float y_m, float z_m)
{
    mavlink_set_position_target_local_ned_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.target_component = MAV_DEFAULT_TARG_COMPONENT;
    com.coordinate_frame = MAV_FRAME_BODY_NED;
    com.type_mask = TYPE_MASK_USE_POSITION;
    com.x = x_m;
    com.y = y_m;
    com.z = z_m;
    // Encode
    mavlink_message_t message;
    mavlink_msg_set_position_target_local_ned_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}

/**
 * @brief Get command to move with specified velocity in m/s
 *
 * @param x_ms Velocity in m/s to move in X axis
 * @param y_ms Velocity in m/s to move in Y axis
 * @param z_ms Velocity in m/s to move in Z axis
 */
void mav_get_msg_ned_speed_body(unsigned char *res_buf, unsigned int *len, float x_ms, float y_ms, float z_ms)
{
    mavlink_set_position_target_local_ned_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.target_component = MAV_DEFAULT_TARG_COMPONENT;
    com.coordinate_frame = MAV_FRAME_LOCAL_OFFSET_NED;
    com.type_mask = TYPE_MASK_USE_VELOCITY;
    com.vx = x_ms;
    com.vy = y_ms;
    com.vz = z_ms;
    // Encode
    mavlink_message_t message;
    mavlink_msg_set_position_target_local_ned_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}

/**
 * @brief Get command to move with specified velocity in m/s. Use heading.
 *
 * @param x_ms Velocity in m/s to move in X axis
 * @param y_ms Velocity in m/s to move in Y axis
 * @param z_ms Velocity in m/s to move in Z axis
 */
void mav_get_msg_ned_speed(unsigned char *res_buf, unsigned int *len, float x_ms, float y_ms, float z_ms)
{
    mavlink_set_position_target_local_ned_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.target_component = MAV_DEFAULT_TARG_COMPONENT;
    com.coordinate_frame = MAV_FRAME_LOCAL_OFFSET_NED;
    com.type_mask = TYPE_MASK_USE_VELOCITY;
    com.vx = x_ms;
    com.vy = y_ms;
    com.vz = z_ms;
    // Encode
    mavlink_message_t message;
    mavlink_msg_set_position_target_local_ned_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}

void mav_get_msg_targ_global_position(unsigned char *res_buf, unsigned int *len, float lat, float lon, float alt)
{
    mavlink_set_position_target_global_int_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.target_component = MAV_DEFAULT_TARG_COMPONENT;
    com.coordinate_frame = MAV_FRAME_GLOBAL_TERRAIN_ALT_INT;
    com.type_mask = TYPE_MASK_USE_POSITION;
    com.lat_int = (int32_t)(lat * LAT_LON_SCALE);
    com.lon_int = (int32_t)(lon * LAT_LON_SCALE);
    printf("lat %d\t", com.lat_int);
    printf("lon %d\n", com.lon_int);
    com.alt = alt;
    // Encode
    mavlink_message_t message;
    mavlink_msg_set_position_target_global_int_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}

void mav_get_msg_get_global_position(unsigned char *res_buf, unsigned int *len)
{
    mavlink_command_long_t com = {0};
    com.target_system = MAV_DEFAULT_TARG_SYS;
    com.target_component = MAV_DEFAULT_TARG_COMPONENT;
    com.command = MAV_CMD_REQUEST_MESSAGE;
    com.param1 = MAVLINK_MSG_ID_GLOBAL_POSITION_INT;
    // Encode
    mavlink_message_t message;
    mavlink_msg_command_long_encode(SYSTEM_ID,  COMPONENT_ID, &message, &com);
    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}




void mav_get_msg_ned_attitude(unsigned char *res_buf, unsigned int *len, float roll_angle, float pitch_angle, float yaw_angle)
{
    mavlink_set_attitude_target_t com = {0};
  //com.g = {1, 0, 0, 0};       //  zero-rotation 
    com.time_boot_ms = 0;       //  timestamp
    com.target_system = 0;      //  System ID
    com.target_component = 0;   //  Component ID
 // com.type_mask = TYPE_MASK_USE_VELOCITY;
    com.body_roll_rate = 0;     // [rad/s]
    com.body_roll_rate = 0;
    com.body_yaw_rate = 0; 
    com.thrust = 0.5;
    mavlink_euler_to_quaternion(roll_angle, pitch_angle, yaw_angle, com.q);
  
    // Encode
    mavlink_message_t message;

    mavlink_msg_set_attitude_target_encode(SYSTEM_ID, COMPONENT_ID, &message, &com);

    *len = mavlink_msg_to_send_buffer(res_buf,
                                      &message);
}


