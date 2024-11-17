import rclpy
from rclpy.node import Node 
from sensor_msgs.msg import Image 
from cv_bridge import CvBridge 
import cv2 as cv
from top_view_visualization.GoProInterface.webcam import GoProWebcamPlayer
from top_view_visualization.camera_calibration.opencv_calibration.camera_distortion import CameraDistortion


class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        self.publisher_ = self.create_publisher(Image, 'scenario_image', 10)
        timer_period = 0.1  # seconds
        self.bridge = CvBridge()
        self.webcam = GoProStream()
        self.cameraDistortion = CameraDistortion()
        self.webcam.start_stream() #starts the http stream of photos
        self.timer = self.create_timer(timer_period, self.timer_callback) #publish on the topic "scienario_image" every 0.1 seconds 


    def timer_callback(self):
        ret, frame = self.webcam.image_capture() #acts as openCV's cap.read() which returns a boolean and numpy array represetning the image
        # frame = cv.imread("src/top_view_visualization/top_view_visualization/sample.jpg") #sample image for testing purpose
        # ret = True #testing purposes 
        if ret:
            frame = self.cameraDistortion.undistort(frame)
            self.publisher_.publish(self.bridge.cv2_to_imgmsg(frame))
            # self.get_logger().info('Publishing video frame')


def main(args=None):
    rclpy.init(args=args)
    camera_publisher = CameraPublisher()
    rclpy.spin(camera_publisher)
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    camera_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()




class GoProStream:
    """
    Initialize an object to stream gopro video as a webcam, serial number is the last three numbers of the serial, port is the http port you want to send on
    """
    def __init__(self, serial_number: list[int] = [5,3,7], port: int = 9000):
        self.serial_number = serial_number
        self.port = port
        self.webcam = GoProWebcamPlayer([5,3,7], 9000)
    """
    Starts video stream
    ros2_send toggles between sending over a topic and displaying with opencv.
    """
    def start_stream(self):
        self.webcam.open()
        self.webcam.play()

    def image_capture(self):
        cap = cv.VideoCapture(f'udp://127.0.0.1:{self.port}',cv.CAP_FFMPEG)
        ret, frame = cap.read()
        return ret, frame
