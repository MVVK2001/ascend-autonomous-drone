#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import String

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray


class NavigationNode(Node):

    def __init__(self):

        super().__init__('navigation_node')

        # Mission State
        self.mission_state = "IDLE"

        # Publishers
        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/current_pose',
            10)

        self.goal_pub = self.create_publisher(
            PoseStamped,
            '/goal_pose',
            10)

        self.path_pub = self.create_publisher(
            Path,
            '/planned_path',
            10)

        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/waypoint_markers',
            10)

        # Subscriber
        self.state_sub = self.create_subscription(
            String,
            '/mission_state',
            self.state_callback,
            10)

        # ASCEND Mission Waypoints
        self.waypoints = [
            (0.0, 0.0, 2.0),   # HOME
            (5.0, 0.0, 2.0),   # WP1
            (5.0, 5.0, 2.0),   # WP2
            (0.0, 5.0, 2.0),   # WP3
            (0.0, 0.0, 2.0)    # RETURN HOME
        ]

        self.current_wp = 1

        # Simulated Drone Position
        self.x = 0.0
        self.y = 0.0
        self.z = 2.0

        self.step_size = 0.1

        # Path Message
        self.path_msg = Path()
        self.path_msg.header.frame_id = "map"

        self.timer = self.create_timer(
            0.1,
            self.update)

        self.get_logger().info(
            "ASCEND Navigation Node Started")

    def state_callback(self, msg):

        if self.mission_state != msg.data:

            self.mission_state = msg.data

            self.get_logger().info(
                f"Mission State Changed -> {self.mission_state}"
            )

    def publish_waypoints(self):

        marker_array = MarkerArray()

        for i, wp in enumerate(self.waypoints):

            marker = Marker()

            marker.header.frame_id = "map"
            marker.header.stamp = self.get_clock().now().to_msg()

            marker.ns = "waypoints"
            marker.id = i

            marker.type = Marker.SPHERE
            marker.action = Marker.ADD

            marker.pose.position.x = wp[0]
            marker.pose.position.y = wp[1]
            marker.pose.position.z = wp[2]

            marker.pose.orientation.w = 1.0

            marker.scale.x = 0.4
            marker.scale.y = 0.4
            marker.scale.z = 0.4

            marker.color.a = 1.0

            if i == 0:
                # HOME
                marker.color.r = 0.0
                marker.color.g = 1.0
                marker.color.b = 0.0
            else:
                # WAYPOINTS
                marker.color.r = 1.0
                marker.color.g = 0.0
                marker.color.b = 0.0

            marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)

    def publish_goal_pose(self, x, y, z):

        goal = PoseStamped()

        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = z

        goal.pose.orientation.w = 1.0

        self.goal_pub.publish(goal)

    def move_to_target(self, target_x, target_y):

        dx = target_x - self.x
        dy = target_y - self.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.15:
            return True

        self.x += self.step_size * dx / distance
        self.y += self.step_size * dy / distance

        return False

    def publish_current_pose(self):

        pose = PoseStamped()

        pose.header.frame_id = "map"
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = self.x
        pose.pose.position.y = self.y
        pose.pose.position.z = self.z

        pose.pose.orientation.w = 1.0

        self.pose_pub.publish(pose)

        self.path_msg.header.stamp = \
            self.get_clock().now().to_msg()

        self.path_msg.poses.append(pose)

        self.path_pub.publish(self.path_msg)

    def update(self):

        self.publish_waypoints()

        # IDLE
        if self.mission_state == "IDLE":

            self.publish_current_pose()
            return

        # TAKEOFF
        elif self.mission_state == "TAKEOFF":

            self.publish_current_pose()
            return

        # SEARCH
        elif self.mission_state == "SURVEY":

            target_x, target_y, target_z = \
                self.waypoints[self.current_wp]

            self.publish_goal_pose(
                target_x,
                target_y,
                target_z)

            reached = self.move_to_target(
                target_x,
                target_y)

            if reached:

                self.get_logger().info(
                    f"Reached WP {self.current_wp}"
                )

                self.current_wp += 1

                if self.current_wp >= len(self.waypoints):

                    self.current_wp = 1

        # RETURN HOME
        elif self.mission_state == "RETURN_HOME":

            target_x = 0.0
            target_y = 0.0
            target_z = 2.0

            self.publish_goal_pose(
                target_x,
                target_y,
                target_z)

            self.move_to_target(
                target_x,
                target_y)

        # DOCK
        elif self.mission_state == "DOCK":

            pass

        # CHARGE
        elif self.mission_state == "CHARGE":

            pass

        self.publish_current_pose()


def main(args=None):

    rclpy.init(args=args)

    node = NavigationNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
