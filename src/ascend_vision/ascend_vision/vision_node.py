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

        # Mission State
        self.mission_state = "IDLE"

        # Current Pose
        self.current_pose = None

        # Image Counter
        self.image_count = 0

        # Prevent Duplicate Captures
        self.captured_waypoints = set()
        self.bridge = CvBridge() 

        # Storage Paths
        self.hd_dir = "/home/administrator/ascend_data/hd_images"
        self.lr_dir = "/home/administrator/ascend_data/lr_images"
        self.metadata_dir = "/home/administrator/ascend_data/metadata"

        # Test Image Directory
        self.test_image_dir = \
            "/home/administrator/ascend_ws/src/ascend_vision/test_images"

        # Image Mapping
        self.image_map = {
            1: "high_day.jpg",
            2: "mid_day.jpg",
            3: "low_day.jpg"
        }

        # Subscribers
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

        # Publishers
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
            '/vision/latest_image',
            10
        )

        self.get_logger().info(
            "ASCEND Vision Node Started"
        )
        
        self.last_image_msg = None 
        
        self.create_timer(
            1.0,
            self.publish_latest_image
        )

    def state_callback(self, msg):

        self.mission_state = msg.data

    def pose_callback(self, msg):

        self.current_pose = msg

    def waypoint_callback(self, msg):

        waypoint_id = msg.data

        if self.mission_state != "SURVEY":
            return

        if waypoint_id not in [1, 2, 3]:
            return

        if waypoint_id in self.captured_waypoints:
            return

        self.captured_waypoints.add(waypoint_id)

        self.capture_image(waypoint_id)

    def capture_image(self, waypoint_id):

        image_name = self.image_map[waypoint_id]

        image_path = os.path.join(
            self.test_image_dir,
            image_name
        )

        image = cv2.imread(image_path)

        if image is None:

            self.get_logger().error(
                f"Could not load image: {image_path}"
            )

            return

        self.image_count += 1

        image_id = f"{self.image_count:03d}"

        # Save HD Image
        hd_path = os.path.join(
            self.hd_dir,
            f"image_{image_id}.jpg"
        )

        cv2.imwrite(hd_path, image)

        # Create LR Image
        lr_image = cv2.resize(
            image,
            (640, 360),
            interpolation=cv2.INTER_AREA
        )

        lr_path = os.path.join(
            self.lr_dir,
            f"image_{image_id}_lr.jpg"
        )

        cv2.imwrite(lr_path, lr_image)
        
        # Publish image to RViz

        self.last_image_msg = self.bridge.cv2_to_imgmsg(
            lr_image,
            encoding='bgr8'
        )

        self.image_pub.publish(self.last_image_msg)

        # Metadata
        metadata = {
            "image_id": self.image_count,
            "waypoint": waypoint_id,
            "mission_state": self.mission_state,
            "timestamp": datetime.now().isoformat()
        }

        if self.current_pose is not None:

            metadata["position"] = {
                "x": self.current_pose.pose.position.x,
                "y": self.current_pose.pose.position.y,
                "z": self.current_pose.pose.position.z
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

        # Publish Count
        count_msg = Int32()
        count_msg.data = self.image_count

        self.image_count_pub.publish(count_msg)

        # Publish Status
        status_msg = String()
        status_msg.data = \
            f"Captured Image {self.image_count} at WP{waypoint_id}"

        self.status_pub.publish(status_msg)

        self.get_logger().info(
            status_msg.data
        )
        
    def publish_latest_image(self):
         if self.last_image_msg is not None:
             self.image_pub.publish(
                 self.last_image_msg
             )


def main(args=None):

    rclpy.init(args=args)

    node = VisionNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
