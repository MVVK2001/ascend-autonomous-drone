#!/usr/bin/env python3

import cv2

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class CameraNode(Node):

    def __init__(self):

        super().__init__('camera_node')

        self.bridge = CvBridge()

        self.publisher = self.create_publisher(
            Image,
            '/vision/latest_image',
            10
        )

        self.pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! "
            "nvvidconv ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! appsink"
        )

        self.cap = cv2.VideoCapture(
            self.pipeline,
            cv2.CAP_GSTREAMER
        )

        if not self.cap.isOpened():

            self.get_logger().error(
                'Failed to open IMX477 camera'
            )

            return

        self.get_logger().info(
            'IMX477 camera opened'
        )

        self.timer = self.create_timer(
            0.1,
            self.publish_frame
        )

    def publish_frame(self):

        ret, frame = self.cap.read()

        if not ret:
            return

        msg = self.bridge.cv2_to_imgmsg(
            frame,
            encoding='bgr8'
        )

        self.publisher.publish(msg)

    def destroy_node(self):

        if self.cap.isOpened():
            self.cap.release()

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = CameraNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
