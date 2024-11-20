import numpy as np
import cv2 as cv
import glob
import pickle
import os
def get_images(delete_prev_photos=False):
    if not os.path.exists("./calibration_images"):
        os.makedirs("./calibration_images")
    if delete_prev_photos:
        files = glob.glob('./calibration_images/*')
        for f in files:
            os.remove(f)
    cap = cv.VideoCapture(1) # video capture source camera (Here webcam of laptop) 
    ret,frame = cap.read()
    image_number = 0;      
    while cap.isOpened():
        ret, frame = cap.read()
        cv.imshow(f'img{image_number}',frame) #display the captured image
        if cv.waitKey(1) & 0xFF == ord('y'): #save on pressing 'y' 
            cv.imwrite(f'calibration_images/picture_{image_number}.jpg',frame)
            cv.destroyAllWindows()
            image_number += 1
        if cv.waitKey(1) & 0xFF == ord('q'): #quit by pressing q
            cv.destroyAllWindows()
            break
    cap.release()

def calibrate_and_save(internal_corner_row, internal_corner_col):
    CHECKERBOARD = (internal_corner_row,internal_corner_col)
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
    objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2)
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.
    images = glob.glob('./calibration_images/*.jpg')
    for fname in images:
        img = cv.imread(fname)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, (CHECKERBOARD[0],CHECKERBOARD[1]), None)
        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)
            corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
            cv.drawChessboardCorners(img, (CHECKERBOARD[0],CHECKERBOARD[1]), corners2, ret)

    cv.destroyAllWindows()
    print("starting callibration")
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    print("ending callibration")

    pickle.dump((mtx, dist), open("./calibration/calibration.pkl", "wb"))
    pickle.dump(mtx, open("./calibration/cameraMatrix.pkl", "wb"))
    pickle.dump(dist, open("./calibration/dist.pkl", "wb"))
if __name__ == "__main__":
    get_images(delete_prev_photos=True)
    calibrate_and_save()

