import cv2 as cv
from GoProInterface import GoProWebcamPlayer
from cv_bridge import CvBridge

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
    ros2_send = True: send over topic
    ros2_send = False: display on opencv GUI
    press 'q' to stop the stream
    """
    def start_stream(self, ros2_send: bool = True):
        self.webcam.open()
        self.webcam.play()
        self.image_capture(ros2_send)
        self.webcam.close()

    def image_capture(self, ros2_send):
        cap = cv.VideoCapture(f'udp://127.0.0.1:{self.port}',cv.CAP_FFMPEG)
        if not cap.isOpened():
            print('VideoCapture not opened')
            exit(-1)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if (not ros2_send):
                cv.imshow('image', frame)
            else:
                bridge = CvBridge()
                image_message = bridge.cv2_to_imgmsg(frame, encoding="passthrough")
            if cv.waitKey(1)&0XFF == ord('q'):
                break
        cap.release()
        cv.destroyAllWindows()
def main():
    stream = GoProStream()
    stream.start_stream(ros2_send=False)
    

if __name__ == "__main__":
    main()
