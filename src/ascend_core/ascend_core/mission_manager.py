#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from std_msgs.msg import Bool


class MissionManager(Node):

    def __init__(self):

        super().__init__('mission_manager')

        # ==========================================
        # Publisher
        # ==========================================

        self.state_pub = self.create_publisher(
            String,
            '/mission_state',
            10
        )

        # ==========================================
        # Navigation Event Subscribers
        # ==========================================

        self.takeoff_sub = self.create_subscription(
            Bool,
            '/navigation/takeoff_complete',
            self.takeoff_callback,
            10
        )

        self.overview_sub = self.create_subscription(
            Bool,
            '/navigation/overview_complete',
            self.overview_callback,
            10
        )
        
        self.descend_sub = self.create_subscription(
            Bool,
            '/navigation/descend_complete',
            self.descend_callback,
            10
        )

        self.survey_sub = self.create_subscription(
            Bool,
            '/navigation/survey_complete',
            self.survey_callback,
            10
        )

        self.home_sub = self.create_subscription(
            Bool,
            '/navigation/home_reached',
            self.home_callback,
            10
        )

        self.landed_sub = self.create_subscription(
            Bool,
            '/navigation/landed',
            self.landed_callback,
            10
        )

        # ==========================================
        # Mission State
        # ==========================================

        self.current_state = "IDLE"

        self.takeoff_complete = False
        self.overview_complete = False
        self.descend_complete = False
        self.survey_complete = False
        self.home_reached = False
        self.landed = False

        self.start_time = self.get_clock().now()

        self.timer = self.create_timer(
            1.0,
            self.update
        )

        self.get_logger().info(
            "ASCEND Mission Manager Started"
        )

    # ==========================================
    # Navigation Event Callbacks
    # ==========================================

    def takeoff_callback(self, msg):

        self.takeoff_complete = msg.data

    def overview_callback(self, msg):

        self.overview_complete = msg.data

    def descend_callback(self, msg):

        self.descend_complete = msg.data
    
    def survey_callback(self, msg):

        self.survey_complete = msg.data

    def home_callback(self, msg):

        self.home_reached = msg.data

    def landed_callback(self, msg):

        self.landed = msg.data

    # ==========================================
    # Utilities
    # ==========================================

    def publish_state(self):

        msg = String()
        msg.data = self.current_state

        self.state_pub.publish(msg)

    def elapsed(self):

        now = self.get_clock().now()

        return (
            now.nanoseconds -
            self.start_time.nanoseconds
        ) / 1e9

    def change_state(self, new_state):

        self.current_state = new_state

        self.start_time = self.get_clock().now()

        self.get_logger().info(
            f"State Changed -> {new_state}"
        )
        
        #Reset event flags
        self.takeoff_complete = False
        self.overview_complete = False
        self.descend_complete = False
        self.survey_complete = False
        self.home_reached = False
        self.landed = False

    # ==========================================
    # Main State Machine
    # ==========================================

    def update(self):

        # -------------------------------
        # IDLE
        # -------------------------------

        if self.current_state == "IDLE":

            if self.elapsed() > 5:

                self.change_state(
                    "TAKEOFF"
                )

        # -------------------------------
        # TAKEOFF
        # -------------------------------

        elif self.current_state == "TAKEOFF":

            if self.takeoff_complete:

                self.change_state(
                    "OVERVIEW_CAPTURE"
                )

        # -------------------------------
        # OVERVIEW_CAPTURE
        # -------------------------------

        elif self.current_state == "OVERVIEW_CAPTURE":

            if self.overview_complete:

                self.change_state(
                    "DESCEND_TO_SURVEY"
                )

        elif self.current_state == "DESCEND_TO_SURVEY":

            if self.descend_complete:

                self.change_state(
                    "SURVEY"
                )
        
        # -------------------------------
        # SURVEY
        # -------------------------------

        elif self.current_state == "SURVEY":

            if self.survey_complete:

                self.change_state(
                    "RETURN_HOME"
                )

        # -------------------------------
        # RETURN_HOME
        # -------------------------------

        elif self.current_state == "RETURN_HOME":

            if self.home_reached:

                self.change_state(
                    "LAND"
                )

        # -------------------------------
        # LAND
        # -------------------------------

        elif self.current_state == "LAND":

            if self.landed:

                self.change_state(
                    "DOCK"
                )

        # -------------------------------
        # DOCK
        # -------------------------------

        elif self.current_state == "DOCK":

            if self.elapsed() > 5:

                self.change_state(
                    "CHARGE"
                )

        # -------------------------------
        # CHARGE
        # -------------------------------

        elif self.current_state == "CHARGE":

            if self.elapsed() > 10:

                self.change_state(
                    "TRANSFER_DATA"
                )

        # -------------------------------
        # TRANSFER_DATA
        # -------------------------------

        elif self.current_state == "TRANSFER_DATA":

            if self.elapsed() > 5:

                self.change_state(
                    "MISSION_COMPLETE"
                )

        self.publish_state()

    # ==========================================


def main(args=None):

    rclpy.init(args=args)

    node = MissionManager()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()
