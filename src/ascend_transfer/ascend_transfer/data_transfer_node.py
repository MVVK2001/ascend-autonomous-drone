#!/usr/bin/env python3

import os
import json
import shutil

from datetime import datetime

import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class DataTransferNode(Node):

    def __init__(self):

        super().__init__('data_transfer_node')

        # ==========================================
        # Paths
        # ==========================================

        self.drone_data_dir = \
            "/home/administrator/ascend_data"

        self.base_station_dir = \
            "/home/administrator/base_station/missions"

        # ==========================================
        # Mission State
        # ==========================================

        self.mission_state = "IDLE"

        self.transfer_completed = False

        # ==========================================
        # Subscriber
        # ==========================================

        self.state_sub = self.create_subscription(
            String,
            '/mission_state',
            self.state_callback,
            10
        )

        # ==========================================
        # Publisher
        # ==========================================

        self.status_pub = self.create_publisher(
            String,
            '/transfer/status',
            10
        )

        self.publish_status("WAITING")

        self.get_logger().info(
            "ASCEND Data Transfer Node Started"
        )

    # ==========================================
    # Mission State Callback
    # ==========================================

    def state_callback(self, msg):

        self.mission_state = msg.data

        if self.mission_state == "IDLE":

            self.transfer_completed = False

        if (
            self.mission_state == "TRANSFER_DATA"
            and not self.transfer_completed
        ):

            self.transfer_completed = True

            self.perform_transfer()

    # ==========================================
    # Status Publisher
    # ==========================================

    def publish_status(self, status):

        msg = String()

        msg.data = status

        self.status_pub.publish(msg)

    # ==========================================
    # Determine Mission Folder
    # ==========================================

    def get_next_mission_folder(self):

        os.makedirs(
            self.base_station_dir,
            exist_ok=True
        )

        existing = [
            d for d in os.listdir(self.base_station_dir)
            if d.startswith("mission_")
        ]

        if not existing:

            mission_number = 1

        else:

            numbers = [
                int(d.split("_")[1])
                for d in existing
            ]

            mission_number = max(numbers) + 1

        mission_name = \
            f"mission_{mission_number:03d}"

        mission_path = os.path.join(
            self.base_station_dir,
            mission_name
        )

        return mission_name, mission_path

    # ==========================================
    # File Copy Helper
    # ==========================================

    def copy_directory_contents(
        self,
        source_dir,
        destination_dir
    ):

        count = 0

        if not os.path.exists(source_dir):
            return 0

        for file_name in os.listdir(source_dir):

            src = os.path.join(
                source_dir,
                file_name
            )

            dst = os.path.join(
                destination_dir,
                file_name
            )

            if os.path.isfile(src):

                shutil.copy2(
                    src,
                    dst
                )

                count += 1

        return count

    # ==========================================
    # Main Transfer Logic
    # ==========================================

    def perform_transfer(self):

        try:

            self.publish_status(
                "TRANSFERRING"
            )

            mission_id, mission_path = \
                self.get_next_mission_folder()

            # Create mission structure

            images_dir = os.path.join(
                mission_path,
                "images"
            )

            metadata_dir = os.path.join(
                mission_path,
                "metadata"
            )

            logs_dir = os.path.join(
                mission_path,
                "logs"
            )

            reports_dir = os.path.join(
                mission_path,
                "reports"
            )

            validation_dir = os.path.join(
                mission_path,
                "validation"
            )

            for folder in [
                images_dir,
                metadata_dir,
                logs_dir,
                reports_dir,
                validation_dir
            ]:

                os.makedirs(
                    folder,
                    exist_ok=True
                )

            # ==================================
            # Copy Images
            # ==================================

            image_count = \
                self.copy_directory_contents(
                    os.path.join(
                        self.drone_data_dir,
                        "lr_images"
                    ),
                    images_dir
                )

            # ==================================
            # Copy Metadata
            # ==================================

            metadata_count = \
                self.copy_directory_contents(
                    os.path.join(
                        self.drone_data_dir,
                        "metadata"
                    ),
                    metadata_dir
                )

            # ==================================
            # Copy Logs
            # ==================================

            log_count = \
                self.copy_directory_contents(
                    os.path.join(
                        self.drone_data_dir,
                        "logs"
                    ),
                    logs_dir
                )

            # ==================================
            # Transfer Report
            # ==================================

            report = {

                "mission_id":
                    mission_id,

                "images_transferred":
                    image_count,

                "metadata_transferred":
                    metadata_count,

                "log_files_transferred":
                    log_count,

                "status":
                    "SUCCESS",

                "timestamp":
                    datetime.now().isoformat()
            }

            report_file = os.path.join(
                reports_dir,
                "transfer_report.json"
            )

            with open(
                report_file,
                'w'
            ) as file:

                json.dump(
                    report,
                    file,
                    indent=4
                )

            self.publish_status(
                "COMPLETED"
            )

            self.get_logger().info(
                f"Transfer Complete -> "
                f"{mission_id}"
            )

        except Exception as e:

            self.publish_status(
                "FAILED"
            )

            self.get_logger().error(
                f"Transfer Failed: {str(e)}"
            )


def main(args=None):

    rclpy.init(args=args)

    node = DataTransferNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()
