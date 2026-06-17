#!/usr/bin/env python3

import os
import cv2
import json

from datetime import datetime

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from std_msgs.msg import Int32

from geometry_msgs.msg import PoseStamped

from sensor_msgs.msg import Image

from cv_bridge import CvBridge


class VisionNode(Node):

    def __init__(self):

        super().__init__('vision_node')

        # ==================================================
        # Mission State
        # ==================================================

        self.mission_state = "IDLE"

        # ==================================================
        # Current Pose
        # ==================================================

        self.current_pose = None

        # ==================================================
        # Image Counters
        # ==================================================

        self.image_count = 0

        self.overview_captured = False

        self.captured_waypoints = set()

        self.bridge = CvBridge()

        self.last_image_msg = None
        self.latest_frame = None

        # ==================================================
        # Storage Paths
        # ==================================================

        self.hd_dir = \
            "/home/administrator/ascend_data/hd_images"

        self.lr_dir = \
            "/home/administrator/ascend_data/lr_images"

        self.metadata_dir = \
            "/home/administrator/ascend_data/metadata"

        os.makedirs(
            self.hd_dir,
            exist_ok=True
        )
        
        os.makedirs(
            self.lr_dir,
            exist_ok=True
        )
        
        os.makedirs(
            self.metadata_dir,
            exist_ok=True
        )
        
        # ==================================================
        # Test Images
        # ==================================================

        self.test_image_dir = \
            "/home/administrator/ascend_ws/src/ascend_vision/test_images"

        self.image_pool = [

            "high_day.jpg",
            "mid_day.jpg",
            "low_day.jpg",

            "high_night.jpg",
            "mid_night.jpg",
            "low_night.jpg",

            "random_1.jpg",
            "random_2.jpg"
        ]

        # ==================================================
        # Subscribers
        # ==================================================

        self.state_sub = self.create_subscription(
            String,
            '/mission_state',
            self.state_callback,
            10
        )

        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/current_pose',
            self.pose_callback,
            10
        )

        self.wp_sub = self.create_subscription(
            Int32,
            '/waypoint_reached',
            self.waypoint_callback,
            10
        )
        
        self.camera_sub = self.create_subscription(
            Image,
            '/vision/latest_image',
            self.image_callback,
            10
        )

        # ==================================================
        # Publishers
        # ==================================================

        self.image_count_pub = self.create_publisher(
            Int32,
            '/vision/image_count',
            10
        )

        self.status_pub = self.create_publisher(
            String,
            '/vision/capture_status',
            10
        )

        self.image_pub = self.create_publisher(
            Image,
            '/vision/preview_image',
            10
        )

        # ==================================================
        # Timer
        # ==================================================

        self.create_timer(
            1.0,
            self.publish_latest_image
        )
        
        self.create_timer(
            15.0,
            self.capture_overview_image
        )

        self.get_logger().info(
            "ASCEND Vision Node Started"
        )

    # ==================================================
    # Mission State
    # ==================================================

    def state_callback(self, msg):

        previous_state = self.mission_state

        self.mission_state = msg.data

        self.get_logger().info(
            f"Vision State -> {self.mission_state}"
        )
        # Capture overview image once

        if (
            self.mission_state == "OVERVIEW_CAPTURE"
            and
            not self.overview_captured
        ):

            self.get_logger().info(
                "Triggering Overview Capture"
            )
            self.capture_overview_image()

        # Reset when mission returns to IDLE

        if (
            previous_state != "IDLE"
            and
            self.mission_state == "IDLE"
        ):

            self.captured_waypoints.clear()

            self.overview_captured = False

            self.image_count = 0

    # ==================================================
    # Pose Callback
    # ==================================================

    def pose_callback(self, msg):

        self.current_pose = msg

    def image_callback(self, msg):

        self.last_image_msg = msg

        try:

            self.latest_frame = \
                self.bridge.imgmsg_to_cv2(
                    msg,
                    desired_encoding='bgr8'
                )

        except Exception as e:

            self.get_logger().error(
                f"Image conversion failed: {e}"
            )
    
    # ==================================================
    # Waypoint Callback
    # ==================================================

    def waypoint_callback(self, msg):

        waypoint_id = msg.data

        if self.mission_state != "SURVEY":
            return

        if waypoint_id < 1:
            return

        if waypoint_id > 17:
            return

        if waypoint_id in self.captured_waypoints:
            return

        self.captured_waypoints.add(
            waypoint_id
        )

        self.capture_image(
            waypoint_id
        )

    # ==================================================
    # Overview Image Capture
    # ==================================================

    def capture_overview_image(self):

        if self.latest_frame is None:

            self.get_logger().warn(
                "No camera image available"
            )

            return

        image = self.latest_frame.copy()

        # ---------------------------------
        # Save HD
        # ---------------------------------

        hd_path = os.path.join(
            self.hd_dir,
            "overview.jpg"
        )

        cv2.imwrite(
            hd_path,
            image
        )

        # ---------------------------------
        # Save LR
        # ---------------------------------

        lr_image = cv2.resize(
            image,
            (640, 360),
            interpolation=cv2.INTER_AREA
        )

        lr_path = os.path.join(
            self.lr_dir,
            "overview_lr.jpg"
        )

        cv2.imwrite(
            lr_path,
            lr_image
        )

        # ---------------------------------
        # Publish to RViz
        # ---------------------------------

        self.last_image_msg = \
            self.bridge.cv2_to_imgmsg(
                lr_image,
                encoding='bgr8'
            )

        self.image_pub.publish(
            self.last_image_msg
        )

        # ---------------------------------
        # Metadata
        # ---------------------------------

        metadata = {

            "image_type": "overview",

            "camera_source":
                "IMX477",
            
            "timestamp":
                datetime.now().isoformat()
        }

        if self.current_pose is not None:

            metadata["position"] = {

                "x":
                    self.current_pose.pose.position.x,

                "y":
                    self.current_pose.pose.position.y,

                "z":
                    self.current_pose.pose.position.z
            }

        metadata_path = os.path.join(
            self.metadata_dir,
            "overview_metadata.json"
        )

        with open(metadata_path, "w") as f:

            json.dump(
                metadata,
                f,
                indent=4
            )

        self.overview_captured = True
        
        self.get_logger().info(
            "Overview Image Captured"
        )

    # ==================================================
    # Survey Image Capture
    # ==================================================

    def capture_image(self, waypoint_id):

        if self.latest_frame is None:

            self.get_logger().warn(
                "No camera image available"
            )

            return

        image = self.latest_frame.copy()

        self.image_count += 1

        image_id = f"{self.image_count:03d}"

        # ---------------------------------
        # HD Image
        # ---------------------------------

        hd_path = os.path.join(
            self.hd_dir,
            f"image_{image_id}.jpg"
        )

        cv2.imwrite(
            hd_path,
            image
        )

        # ---------------------------------
        # LR Image
        # ---------------------------------

        lr_image = cv2.resize(
            image,
            (640, 360),
            interpolation=cv2.INTER_AREA
        )

        lr_path = os.path.join(
            self.lr_dir,
            f"image_{image_id}_lr.jpg"
        )

        cv2.imwrite(
            lr_path,
            lr_image
        )

        # ---------------------------------
        # RViz Image
        # ---------------------------------

        self.last_image_msg = \
            self.bridge.cv2_to_imgmsg(
                lr_image,
                encoding='bgr8'
            )

        self.image_pub.publish(
            self.last_image_msg
        )

        # ---------------------------------
        # Metadata
        # ---------------------------------

        metadata = {

            "image_type": "survey",
            
            "camera_source":
                "IMX477",

            "image_id":
                self.image_count,

            "waypoint":
                waypoint_id,

            "mission_state":
                self.mission_state,

            "timestamp":
                datetime.now().isoformat()
        }

        if self.current_pose is not None:

            metadata["position"] = {

                "x":
                    self.current_pose.pose.position.x,

                "y":
                    self.current_pose.pose.position.y,

                "z":
                    self.current_pose.pose.position.z
            }

        metadata_path = os.path.join(
            self.metadata_dir,
            f"metadata_{image_id}.json"
        )

        with open(metadata_path, "w") as f:

            json.dump(
                metadata,
                f,
                indent=4
            )

        # ---------------------------------
        # Publish Count
        # ---------------------------------

        count_msg = Int32()

        count_msg.data = \
            self.image_count

        self.image_count_pub.publish(
            count_msg
        )

        # ---------------------------------
        # Publish Status
        # ---------------------------------

        status_msg = String()

        status_msg.data = (
            f"Captured Image "
            f"{self.image_count} "
            f"at WP{waypoint_id}"
        )

        self.status_pub.publish(
            status_msg
        )

        self.get_logger().info(
            status_msg.data
        )

    # ==================================================
    # RViz Image Refresh
    # ==================================================

    def publish_latest_image(self):

        if (
            self.mission_state == "OVERVIEW_CAPTURE"
            and
            not self.overview_captured
        ):

            self.capture_overview_image()

        if self.last_image_msg is not None:

            self.image_pub.publish(
                self.last_image_msg
            )

    # ==================================================


def main(args=None):

    rclpy.init(args=args)

    node = VisionNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()
