#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class MissionManager(Node):

    def __init__(self):

        super().__init__('mission_manager')

        self.state_pub = self.create_publisher(
            String,
            '/mission_state',
            10)

        self.states = [
            "IDLE",
            "TAKEOFF",
            "SURVEY",
            "RETURN_HOME",
            "DOCK",
            "CHARGE",
            "TRANSFER_DATA",
            "MISSION_COMPLETE"
        ]

        self.current_state = "IDLE"

        self.takeoff_complete = False
        self.survey_complete = False
        self.home_reached = False
        self.dock_complete = False
        self.charge_complete = False
        self.transfer_complete = False

        self.start_time = self.get_clock().now()

        self.timer = self.create_timer(
            1.0,
            self.update)

        self.get_logger().info(
            "ASCEND Mission Manager Started")

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

    def update(self):

        # SIMULATION EVENTS

        if self.current_state == "IDLE":

            if self.elapsed() > 5:

                self.current_state = "TAKEOFF"

                self.start_time = self.get_clock().now()

        elif self.current_state == "TAKEOFF":

            if self.elapsed() > 5:

                self.takeoff_complete = True

                self.current_state = "SURVEY"

                self.start_time = self.get_clock().now()

        elif self.current_state == "SURVEY":

            if self.elapsed() > 20:

                self.survey_complete = True

                self.current_state = "RETURN_HOME"

                self.start_time = self.get_clock().now()

        elif self.current_state == "RETURN_HOME":

            if self.elapsed() > 10:

                self.home_reached = True

                self.current_state = "DOCK"

                self.start_time = self.get_clock().now()

        elif self.current_state == "DOCK":

            if self.elapsed() > 5:

                self.dock_complete = True

                self.current_state = "CHARGE"

                self.start_time = self.get_clock().now()

        elif self.current_state == "CHARGE":

            if self.elapsed() > 10:

                self.charge_complete = True

                self.current_state = "TRANSFER_DATA"

                self.start_time = self.get_clock().now()

        elif self.current_state == "TRANSFER_DATA":

            if self.elapsed() > 5:

                self.transfer_complete = True

                self.current_state = "MISSION_COMPLETE"

                self.start_time = self.get_clock().now()

        self.publish_state()

        self.get_logger().info(
            f"Mission State: {self.current_state}"
        )


def main(args=None):

    rclpy.init(args=args)

    node = MissionManager()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
