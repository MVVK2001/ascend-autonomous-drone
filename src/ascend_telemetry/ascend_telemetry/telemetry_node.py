#!/usr/bin/env python3

import rclpy

from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from std_msgs.msg import Float32

from visualization_msgs.msg import Marker


class TelemetryNode(Node):

    def __init__(self):

        super().__init__('telemetry_node')

        self.battery = 100.0

        self.current_pose = None

        self.mission_state = "IDLE"

        # Subscribers

        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/current_pose',
            self.pose_callback,
            10)

        self.state_sub = self.create_subscription(
            String,
            '/mission_state',
            self.state_callback,
            10)

        # Publishers

        self.battery_pub = self.create_publisher(
            Float32,
            '/telemetry/battery',
            10)

        self.marker_pub = self.create_publisher(
            Marker,
            '/telemetry_marker',
            10)

        self.timer = self.create_timer(
            1.0,
            self.update)

        self.get_logger().info(
            "ASCEND Telemetry Node Started")

    def pose_callback(self, msg):

        self.current_pose = msg

    def state_callback(self, msg):

        self.mission_state = msg.data

    def publish_text_marker(self):

        if self.current_pose is None:
            return

        marker = Marker()

        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = "telemetry"

        marker.id = 0

        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD

        marker.pose.position.x = \
            self.current_pose.pose.position.x

        marker.pose.position.y = \
            self.current_pose.pose.position.y

        marker.pose.position.z = \
            self.current_pose.pose.position.z + 1.0

        marker.scale.z = 0.4

        marker.color.a = 1.0
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0

        marker.text = (
            f"State: {self.mission_state}\n"
            f"Battery: {self.battery:.1f}%"
        )

        self.marker_pub.publish(marker)

    def update(self):

        if self.mission_state in [
            "TAKEOFF",
            "SURVEY",
            "RETURN_HOME"
        ]:

            self.battery -= 0.5

        if self.battery < 20:

            self.battery = 20

        battery_msg = Float32()

        battery_msg.data = self.battery

        self.battery_pub.publish(
            battery_msg)

        self.publish_text_marker()

        if self.current_pose is not None:

            self.get_logger().info(
                f"Battery={self.battery:.1f}% | "
                f"State={self.mission_state} | "
                f"X={self.current_pose.pose.position.x:.2f} "
                f"Y={self.current_pose.pose.position.y:.2f}"
            )


def main(args=None):

    rclpy.init(args=args)

    node = TelemetryNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
