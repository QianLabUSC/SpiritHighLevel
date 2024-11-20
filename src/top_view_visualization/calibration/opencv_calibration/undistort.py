import cv2 as cv
import pickle
def undistort(picture_path):
    try:
        mtx = pickle.load(open("./calibration/cameraMatrix.pkl", "rb"))
        dist = pickle.load(open("./calibration/dist.pkl", "rb"))
        img = cv.imread(picture_path)
        h,  w = img.shape[:2]
        newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))

        # undistort
        dst = cv.undistort(img, mtx, dist, None, newcameramtx)
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        cv.imwrite('calibresult.png', dst)
    except:
        print("No calibration/ settings found")
if __name__ == "__main__":
    undistort('./calibration_images/picture_23.jpg')

