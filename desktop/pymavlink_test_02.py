#!/usr/bin/env python

'''
check bandwidth of link
'''
from __future__ import print_function
import time
import asyncio

from pymavlink import mavutil

# using argparse to receive options from the command line
from argparse import ArgumentParser


HEARTBEAT_TIMEOUT_S = 1

master = None
t1 = time.time()
counts = {}
bytes_sent = 0
bytes_recv = 0


def connect():
    global master

    parser = ArgumentParser(description=__doc__)

    parser.add_argument("--baudrate", type=int,
                        help="master port baud rate", default=115200)
    parser.add_argument("--device", required=True, help="serial device")
    args = parser.parse_args()

    ### MAV related code starts here ###

    # create a mavlink serial instance
    master = mavutil.mavlink_connection(args.device, baud=args.baudrate)
    print("Connected to: " + str(master.port))

async def receaver():
    global master
    global t1
    global counts
    global bytes_sent
    global bytes_recv

    while True:
        # Check for incoming data on the serial port and count
        # how many messages of each type have been received
        while master.port.inWaiting() > 0:
            # recv_msg will try parsing the serial port buffer
            # and return a new message if available
            m = master.recv_msg()

            if m is None: break  # No new message

            print(">> " + str(m))

            if m.get_type() not in counts:
                # if no messages of this type received, add this type to the counts dict
                counts[m.get_type()] = 0
                #print(">> " + str(m))

            counts[m.get_type()] += 1

        # Print statistics every second
        t2 = time.time()
        if t2 - t1 > 1.0:
            print("%u sent, %u received, %u errors bwin=%.1f kB/s bwout=%.1f kB/s" % (
                master.mav.total_packets_sent,
                master.mav.total_packets_received,
                master.mav.total_receive_errors,
                0.001 * (master.mav.total_bytes_received - bytes_recv) / (t2 - t1),
                0.001 * (master.mav.total_bytes_sent - bytes_sent) / (t2 - t1)))
            bytes_sent = master.mav.total_bytes_sent
            bytes_recv = master.mav.total_bytes_received
            t1 = t2

        await asyncio.sleep(0.01)


async def sender():
    global master

    # send some messages to the target system with dummy data
    # aster.mav.heartbeat_send(1, 1, 1, 1, 2)
    # master.mav.sys_status_send(1, 2, 3, 4, 5, 6, 7)
    # master.mav.gps_raw_send(1, 2, 3, 4, 5, 6, 7, 8, 9)
    # master.mav.attitude_send(1, 2, 3, 4, 5, 6, 7)
    # master.mav.vfr_hud_send(1, 2, 3, 4, 5, 6)

    await asyncio.sleep(3)

    target_system = 1
    target_component = 191
    master.mav.srcComponent = 25 # master.mav.MAV_COMP_ID_USER1
    master.mav.param_request_list_send(target_system, target_component)
    print(f"_________________<< param_request_list_send(target_system={target_system}, target_component={target_component})")

    while True:
        await asyncio.sleep(0.01)


async def heartbeat():
    while True:
        custom_mode = 15  # /*<  A bitfield for use for autopilot-specific flags*/
        type = 1  # /*<  Vehicle or component type. For a flight controller component the vehicle type (quadrotor, helicopter, etc.). For other components the component type (e.g. camera, gimbal, etc.). This should be used in preference to component id for identifying the component type.*/
        autopilot = 3  # /*<  Autopilot type / class. Use MAV_AUTOPILOT_INVALID for components that are not flight controllers.*/
        base_mode = 217  # /*<  System mode bitmap.*/
        system_status = 4  # /*<  System status flag.*/
        mavlink_version = 2
        master.mav.heartbeat_send(type, autopilot, base_mode, custom_mode, system_status)
        print(f"_________________<< heartbeat_send(type={type}, autopilot={autopilot}, base_mode={base_mode}, custom_mode={custom_mode}, system_status={system_status})")

        await asyncio.sleep(HEARTBEAT_TIMEOUT_S)

async def main():
    connect()

    receaver_task = asyncio.create_task(receaver())
    sender_task = asyncio.create_task(sender())
    heartbeat_task = asyncio.create_task(heartbeat())
    results = await asyncio.gather(receaver_task, sender_task, heartbeat_task)


if __name__ ==  '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())