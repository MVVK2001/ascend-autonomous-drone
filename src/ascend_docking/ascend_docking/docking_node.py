import rclpy

from rclpy.node import Node

from std_msgs.msg import String


class DockingNode(Node):

    def __init__(self):

        super().__init__('docking_node')

        self.state = "IDLE"

        self.create_subscription(
            String,
            '/mission_state',
            self.mission_callback,
            10
        )

        self.docking_state_pub = self.create_publisher(
            String,
            '/docking/state',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_state
        )

        self.get_logger().info(
            'ASCEND Docking Node Started'
        )

    def mission_callback(self, msg):

        if msg.data == "RETURN_HOME":

            self.state = "DOCKING_SEARCH"

            self.get_logger().info(
                'Docking Search Started'
            )

    def publish_state(self):

        msg = String()

        msg.data = self.state

        self.docking_state_pub.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = DockingNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
