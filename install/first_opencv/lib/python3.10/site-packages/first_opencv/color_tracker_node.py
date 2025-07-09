# 导入 ROS2 和图像处理相关模块
import rclpy                                      # ROS2 Python 客户端库
from rclpy.node import Node                       # 用于定义节点基类
from sensor_msgs.msg import Image                 # ROS2 中的图像消息类型
from cv_bridge import CvBridge                    # ROS图像 <-> OpenCV图像 的转换桥梁

import cv2                                        # OpenCV，用于图像处理
import numpy as np                                # Numpy，用于矩阵与数组操作

# 定义一个 ROS2 节点类 ColorTracker
class ColorTracker(Node):
    def __init__(self):
        super().__init__('color_tracker_node')    # 节点名叫 "color_tracker_node"
        self.bridge = CvBridge()                  # 创建一个图像转换桥接器
        # 订阅来自摄像头发布的图像话题 "/image_raw"
        self.sub = self.create_subscription(Image, '/image_raw', self.image_callback, 10)

    # 每次接收到图像消息都会调用这个回调函数
    def image_callback(self, msg):
        # 将 ROS 图像消息转为 OpenCV 的 BGR 图像格式
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # 将 BGR 图像转换为 HSV 色彩空间，便于颜色提取
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 定义红色的 HSV 范围（红色分布在 0-10 和 170-180 两个区段）
        lower1 = np.array([0, 120, 70])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([170, 120, 70])
        upper2 = np.array([180, 255, 255])

        # 生成掩膜图像，只保留在红色区间内的像素
        mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)

        # 对掩膜图像进行形态学操作（去噪：先腐蚀再膨胀）
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # 查找所有轮廓区域（即色块）
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 如果找到了轮廓，就画出最小外接圆并标记坐标
        if contours:
            for c in contours:
                (x, y), radius = cv2.minEnclosingCircle(c)  # 拟合最小外接圆
                if radius > 10:  # 排除太小的噪点
                    # 在原图上画圆圈和标注坐标
                    cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                    cv2.putText(frame, f"({int(x)}, {int(y)})", (int(x)+10, int(y)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    # 在终端打印坐标信息
                    self.get_logger().info(f"Red at ({int(x)}, {int(y)})")

        # 显示处理后的视频窗口（每帧刷新）
        cv2.imshow("Red Tracker", frame)
        cv2.waitKey(1)  # 必须有，不然图像不刷新

# 节点主函数
def main(args=None):
    rclpy.init(args=args)         # 初始化 ROS2 客户端
    node = ColorTracker()         # 创建节点实例
    rclpy.spin(node)              # 节点开始运行并保持活跃
    node.destroy_node()           # 退出时销毁节点
    cv2.destroyAllWindows()       # 关闭 OpenCV 窗口
    rclpy.shutdown()              # 关闭 ROS2 客户端