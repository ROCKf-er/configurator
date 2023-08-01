#ifndef MAV_COMMANDS_H
#define MAV_COMMANDS_H

#include <stdbool.h>

#define MAV_DEFAULT_TARG_SYS 1
#define MAV_DEFAULT_TARG_COMPONENT 1

#define COMPONENT_ID    MAV_COMP_ID_USER1
#define SYSTEM_ID       1 

/**
 * @brief Get mavlink message to enter guided mode
 *
 * */
void mav_get_msg_set_guided(unsigned char *res_buf, unsigned int *len, bool enable);

// ned positioning messages
/**
 * @brief Get command to move to the specified position
 * Positions are relative to the vehicle’s EKF Origin in NED frame
 * I.e x=1,y=2,z=3 is 1m North, 2m East and 3m Down from the origin
 * The EKF origin is the vehicle’s location when it first achieved a good position estimate
 * Velocity and Acceleration are in NED frame
 *
 * @param res_buf resulting byte buffer
 * @param len number of bytes in the message
 * @param x_m X Position in meters (positive is North)
 * @param y_m Y Position in meters (positive is East)
 * @param z_m Z Position in meters (positive is down)
 * @return char* resulting mavling message
 */
void mav_get_msg_ned_position_ekf(unsigned char *res_buf, unsigned int *len, float x_m, float y_m, float z_m);
/**
 * @brief Get command to move to the specified position
 * Positions are relative to the vehicle’s current position
 * I.e. x=1,y=2,z=3 is 1m North, 2m East and 3m below the current position.
 * Velocity and Acceleration are in NED frame
 *
 * @param res_buf resulting byte buffer
 * @param len number of bytes in the message
 * @param x_m X Position in meters (positive is North)
 * @param y_m Y Position in meters (positive is East)
 * @param z_m Z Position in meters (positive is down)
 * @return char* resulting mavling message
 */
void mav_get_msg_ned_position_local_offset(unsigned char *res_buf, unsigned int *len, float x_m, float y_m, float z_m);

/**
 * @brief Get command to move to the specified position
 * Positions are relative to the vehicle’s current position and heading
 * I.e x=1,y=2,z=3 is 1m forward, 2m right and 3m Down from the current position
 * Velocity and Acceleration are relative to the current vehicle heading.
 * Use this to specify the speed forward, right and down (or the opposite if you use negative values).
 * Specify yaw rate of zero to stop vehicle yaw from changing
 *
 * @param res_buf resulting byte buffer
 * @param len number of bytes in the message
 * @param x_m X Position in meters (positive is forward)
 * @param y_m Y Position in meters (positive is right)
 * @param z_m Z Position in meters (positive is down)
 * @return char* resulting mavling message
 */
void mav_get_msg_ned_position_body_offset(unsigned char *res_buf, unsigned int *len, float x_m, float y_m, float z_m);

/**
 * @brief Get command to move with specified velocity in m/s
 *
 * @param res_buf resulting byte buffer
 * @param len number of bytes in the message
 * @param x_ms Velocity in m/s to move in X axis
 * @param y_ms Velocity in m/s to move in Y axis
 * @param z_ms Velocity in m/s to move in Z axis
 */
void mav_get_msg_ned_speed_body(unsigned char *res_buf, unsigned int *len, float x_ms, float y_ms, float z_ms);

/**
 * @brief Get command to move with specified velocity in m/s. Use heading.
 *
 * @param x_ms Velocity in m/s to move in X axis
 * @param y_ms Velocity in m/s to move in Y axis
 * @param z_ms Velocity in m/s to move in Z axis
 */
void mav_get_msg_ned_speed(unsigned char *res_buf, unsigned int *len, float x_ms, float y_ms, float z_ms);

/**
 * @brief Get command to move to the specified position in global coordinates.
 *
 * @param res_buf resulting byte buffer
 * @param len number of bytes in the message
 * @param lat target latitude
 * @param lon target longitude
 * @param alt target altitude
 */
void mav_get_msg_targ_global_position(unsigned char *res_buf, unsigned int *len, float lat, float lon, float alt);

void mav_get_msg_get_global_position(unsigned char *res_buf, unsigned int *len);

void mav_get_msg_ned_attitude(unsigned char *res_buf, unsigned int *len, float roll_angle, float pitch_angle, float yaw_angle);

#endif
