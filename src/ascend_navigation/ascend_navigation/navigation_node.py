#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from std_msgs.msg import Int32
from std_msgs.msg import Bool

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray


class NavigationNode(Node):

    def __init__(self):

        super().__init__('navigation_node')

        # ==================================================
        # Mission State
        # ==================================================

        self.mission_state = "IDLE"

        # ==================================================
        # Simulated Drone Position
        # ==================================================

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.step_size = 0.10

        # ==================================================
        # Survey Waypoints
        # ==================================================

        self.waypoints = [

            # Perimeter Loop

            (-5.0,  3.5, 3.0),   # WP1
            ( 5.0,  3.5, 3.0),   # WP2
            ( 5.0, -3.5, 3.0),   # WP3
            (-5.0, -3.5, 3.0),   # WP4
            (-5.0,  3.5, 3.0),   # WP5

            # Interior Serpentine

            (-3.75,  1.75, 3.0), # WP6
            (-1.25,  1.75, 3.0), # WP7
            ( 1.25,  1.75, 3.0), # WP8
            ( 3.75,  1.75, 3.0), # WP9

            ( 3.75,  0.00, 3.0), # WP10
            ( 1.25,  0.00, 3.0), # WP11
            (-1.25,  0.00, 3.0), # WP12
            (-3.75,  0.00, 3.0), # WP13

            (-3.75, -1.75, 3.0), # WP14
            (-1.25, -1.75, 3.0), # WP15
            ( 1.25, -1.75, 3.0), # WP16
            ( 3.75, -1.75, 3.0)  # WP17
        ]

        self.current_wp = 0

        # ==================================================
        # Completion Flags
        # ==================================================

        self.takeoff_sent = False
        self.overview_sent = False
        self.descend_sent = False
        self.survey_sent = False
        self.home_sent = False
        self.landed_sent = False

        # ==================================================
        # Publishers
        # ==================================================

        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/current_pose',
            10
        )

        self.goal_pub = self.create_publisher(
            PoseStamped,
            '/goal_pose',
            10
        )

        self.path_pub = self.create_publisher(
            Path,
            '/planned_path',
            10
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/waypoint_markers',
            10
        )

        self.waypoint_pub = self.create_publisher(
            Int32,
            '/waypoint_reached',
            10
        )

        # ==================================================
        # Navigation Completion Publishers
        # ==================================================

        self.takeoff_pub = self.create_publisher(
            Bool,
            '/navigation/takeoff_complete',
            10
        )

        self.overview_pub = self.create_publisher(
            Bool,
            '/navigation/overview_complete',
            10
        )

        self.descend_pub = self.create_publisher(
            Bool,
            '/navigation/descend_complete',
            10
        )

        self.survey_pub = self.create_publisher(
            Bool,
            '/navigation/survey_complete',
            10
        )

        self.home_pub = self.create_publisher(
            Bool,
            '/navigation/home_reached',
            10
        )

        self.landed_pub = self.create_publisher(
            Bool,
            '/navigation/landed',
            10
        )

        # ==================================================
        # Subscribers
        # ==================================================

        self.state_sub = self.create_subscription(
            String,
            '/mission_state',
            self.state_callback,
            10
        )

        # ==================================================
        # Path Message
        # ==================================================

        self.path_msg = Path()
        self.path_msg.header.frame_id = "map"

        # ==================================================
        # Timer
        # ==================================================

        self.timer = self.create_timer(
            0.1,
            self.update
        )

        self.get_logger().info(
            "ASCEND Navigation Node Started"
        )

    # ==================================================
    # Mission State Callback
    # ==================================================

    def state_callback(self, msg):

        if self.mission_state != msg.data:

            self.mission_state = msg.data

            self.get_logger().info(
                f"Mission State Changed -> {self.mission_state}"
            )

        if msg.data == "IDLE":

            self.current_wp = 0

            self.takeoff_sent = False
            self.overview_sent = False
            self.descend_sent = False
            self.survey_sent = False
            self.home_sent = False
            self.landed_sent = False

            self.path_msg = Path()
            self.path_msg.header.frame_id = "map"

    # ==================================================
    # Utility Functions
    # ==================================================

    def publish_bool(self, publisher):

        msg = Bool()
        msg.data = True

        publisher.publish(msg)

    def move_to_target(
        self,
        target_x,
        target_y,
        target_z
    ):

        dx = target_x - self.x
        dy = target_y - self.y
        dz = target_z - self.z

        distance = math.sqrt(
            dx * dx +
            dy * dy +
            dz * dz
        )

        if distance < 0.15:
            return True

        self.x += self.step_size * dx / distance
        self.y += self.step_size * dy / distance
        self.z += self.step_size * dz / distance

        return False

    # ==================================================
    # RViz Functions
    # ==================================================

    def publish_goal_pose(self, x, y, z):

        goal = PoseStamped()

        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = z

        goal.pose.orientation.w = 1.0

        self.goal_pub.publish(goal)

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

    def publish_waypoints(self):

        marker_array = MarkerArray()

        for i, wp in enumerate(self.waypoints):

            marker = Marker()

            marker.header.frame_id = "map"
            marker.header.stamp = self.get_clock().now().to_msg()

            marker.ns = "survey_waypoints"
            marker.id = i

            marker.type = Marker.SPHERE
            marker.action = Marker.ADD

            marker.pose.position.x = wp[0]
            marker.pose.position.y = wp[1]
            marker.pose.position.z = wp[2]

            marker.pose.orientation.w = 1.0

            marker.scale.x = 0.30
            marker.scale.y = 0.30
            marker.scale.z = 0.30

            marker.color.a = 1.0
            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0

            marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)

    # ==================================================
    # Main Update Loop
    # ==================================================

    def update(self):

        self.publish_waypoints()

        # --------------------------------------------------
        # IDLE
        # --------------------------------------------------

        if self.mission_state == "IDLE":

            self.publish_current_pose()
            return

        # --------------------------------------------------
        # TAKEOFF
        # --------------------------------------------------

        elif self.mission_state == "TAKEOFF":

            reached = self.move_to_target(
                0.0,
                0.0,
                2.0
            )

            self.publish_goal_pose(
                0.0,
                0.0,
                2.0
            )

            if reached and not self.takeoff_sent:

                self.publish_bool(
                    self.takeoff_pub
                )

                self.takeoff_sent = True

        # --------------------------------------------------
        # OVERVIEW_CAPTURE
        # --------------------------------------------------

        elif self.mission_state == "OVERVIEW_CAPTURE":

            reached = self.move_to_target(
                0.0,
                0.0,
                6.0
            )

            self.publish_goal_pose(
                0.0,
                0.0,
                6.0
            )

            if reached and not self.overview_sent:

                self.publish_bool(
                    self.overview_pub
                )

                self.overview_sent = True

        # --------------------------------------------------
        # DESCEND_TO_SURVEY
        # --------------------------------------------------

        elif self.mission_state == "DESCEND_TO_SURVEY":

            reached = self.move_to_target(
                0.0,
                0.0,
                3.0
            )

            self.publish_goal_pose(
                0.0,
                0.0,
                3.0
            )

            if reached and not self.descend_sent:

                self.publish_bool(
                    self.descend_pub
                )

                self.descend_sent = True

        # --------------------------------------------------
        # SURVEY
        # --------------------------------------------------

        elif self.mission_state == "SURVEY":

            if self.current_wp < len(self.waypoints):

                target_x, target_y, target_z = \
                    self.waypoints[self.current_wp]

                self.publish_goal_pose(
                    target_x,
                    target_y,
                    target_z
                )

                reached = self.move_to_target(
                    target_x,
                    target_y,
                    target_z
                )

                if reached:

                    wp_msg = Int32()
                    wp_msg.data = self.current_wp + 1

                    self.waypoint_pub.publish(
                        wp_msg
                    )

                    self.get_logger().info(
                        f"Reached WP {self.current_wp + 1}"
                    )

                    self.current_wp += 1

            else:

                if not self.survey_sent:

                    self.publish_bool(
                        self.survey_pub
                    )

                    self.survey_sent = True

        # --------------------------------------------------
        # RETURN_HOME
        # --------------------------------------------------

        elif self.mission_state == "RETURN_HOME":

            reached = self.move_to_target(
                0.0,
                0.0,
                3.0
            )

            self.publish_goal_pose(
                0.0,
                0.0,
                3.0
            )

            if reached and not self.home_sent:

                self.publish_bool(
                    self.home_pub
                )

                self.home_sent = True

        # --------------------------------------------------
        # LAND
        # --------------------------------------------------

        elif self.mission_state == "LAND":

            reached = self.move_to_target(
                0.0,
                0.0,
                0.0
            )

            self.publish_goal_pose(
                0.0,
                0.0,
                0.0
            )

            if reached and not self.landed_sent:

                self.publish_bool(
                    self.landed_pub
                )

                self.landed_sent = True

        self.publish_current_pose()


def main(args=None):

    rclpy.init(args=args)

    node = NavigationNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()
