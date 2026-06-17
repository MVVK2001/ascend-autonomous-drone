#!/usr/bin/env python3

import os
import csv

from datetime import datetime

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32
from std_msgs.msg import String
from std_msgs.msg import Int32


class TelemetryLogger(Node):

    def __init__(self):

        super().__init__('telemetry_logger')

        # ==================================================
        # Storage Paths
        # ==================================================

        self.logs_dir = "/home/mvvk/ascend_data/logs"

        os.makedirs(
            self.logs_dir,
            exist_ok=True
        )

        self.telemetry_file = os.path.join(
            self.logs_dir,
            "telemetry_log.csv"
        )

        self.events_file = os.path.join(
            self.logs_dir,
            "mission_events.csv"
        )

        # ==================================================
        # Runtime Data
        # ==================================================

        self.current_pose = None
        self.battery = 100.0
        self.mission_state = "IDLE"

        self.previous_state = None

        # ==================================================
        # Create CSV Files
        # ==================================================

        self.initialize_csv_files()

        # ==================================================
        # Subscribers
        # ==================================================

        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/current_pose',
            self.pose_callback,
            10
        )

        self.battery_sub = self.create_subscription(
            Float32,
            '/telemetry/battery',
            self.battery_callback,
            10
        )

        self.state_sub = self.create_subscription(
            String,
            '/mission_state',
            self.state_callback,
            10
        )

        self.wp_sub = self.create_subscription(
            Int32,
            '/waypoint_reached',
            self.waypoint_callback,
            10
        )

        self.capture_sub = self.create_subscription(
            String,
            '/vision/capture_status',
            self.capture_callback,
            10
        )

        # ==================================================
        # Telemetry Logging Timer
        # ==================================================

        self.timer = self.create_timer(
            1.0,
            self.log_telemetry
        )

        self.get_logger().info(
            "ASCEND Telemetry Logger Started"
        )

    # ======================================================
    # CSV Initialization
    # ======================================================

    def initialize_csv_files(self):

        if not os.path.exists(self.telemetry_file):

            with open(
                self.telemetry_file,
                'w',
                newline=''
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
                    "x",
                    "y",
                    "z",
                    "battery",
                    "mission_state"
                ])

        if not os.path.exists(self.events_file):

            with open(
                self.events_file,
                'w',
                newline=''
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
                    "event"
                ])

    # ======================================================
    # Callbacks
    # ======================================================

    def pose_callback(self, msg):

        self.current_pose = msg

    def battery_callback(self, msg):

        self.battery = msg.data

    def state_callback(self, msg):

        self.mission_state = msg.data

        if self.mission_state != self.previous_state:

            if self.mission_state == "MISSION_COMPLETE":
                self.log_event("MISSION_COMPLETE")
            else:
                self.log_event(
                    f"{self.mission_state}_STARTED"
                )

            self.previous_state = self.mission_state

    def waypoint_callback(self, msg):

        self.log_event(
            f"WAYPOINT_{msg.data}_REACHED"
        )

    def capture_callback(self, msg):

        self.log_event(
            msg.data
        )

    # ======================================================
    # Event Logging
    # ======================================================

    def log_event(self, event_text):

        timestamp = datetime.now().isoformat()

        with open(
            self.events_file,
            'a',
            newline=''
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                timestamp,
                event_text
            ])

        self.get_logger().info(
            f"Event Logged: {event_text}"
        )

    # ======================================================
    # Telemetry Logging
    # ======================================================

    def log_telemetry(self):

        if self.current_pose is None:
            return

        if self.mission_state == "MISSION_COMPLETE":
            return
        
        timestamp = datetime.now().isoformat()

        x = self.current_pose.pose.position.x
        y = self.current_pose.pose.position.y
        z = self.current_pose.pose.position.z

        with open(
            self.telemetry_file,
            'a',
            newline=''
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                timestamp,
                round(x, 3),
                round(y, 3),
                round(z, 3),
                round(self.battery, 2),
                self.mission_state
            ])

    # ======================================================


def main(args=None):

    rclpy.init(args=args)

    node = TelemetryLogger()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()
