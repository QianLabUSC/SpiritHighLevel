import cv2 as cv
import pickle
class CameraDistortion:
    def __init__(self):
        try:
            self.mtx = pickle.load(open("top_view_visualization/camera_calibration/calibration/cameraMatrix.pkl", "rb"))
            self.dist = pickle.load(open("top_view_visualization/camera_calibration/calibration/dist.pkl", "rb"))
        except:
            print("No calibration/ settings found")
    def undistort(self, picture_path):
            img = cv.imread(picture_path)
            h,  w = img.shape[:2]
            newcameramtx, roi = cv.getOptimalNewCameraMatrix(self.mtx, self.dist, (w,h), 1, (w,h))
            # undistort
            dst = cv.undistort(img, self.mtx, self.dist, None, newcameramtx)
            # crop the image
            x, y, w, h = roi
            dst = dst[y:y+h, x:x+w]
            cv.imwrite('calibresult.png', dst)