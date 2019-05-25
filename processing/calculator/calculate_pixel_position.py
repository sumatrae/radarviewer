#coding:utf-8
import cv2 as cv
import numpy as np
import glob
import numpy as np
#from .radar_camera_calibration import *



# 找棋盘格角点
# 阈值
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
#棋盘格模板规格
w = 11
h = 8

# 世界坐标系中的棋盘格点,例如(0,0,0), (1,0,0), (2,0,0) ....,(8,5,0)，去掉Z坐标，记为二维矩阵
objp = np.zeros((w*h,3), np.float32)
objp[:,:2] = np.mgrid[0:w,0:h].T.reshape(-1,2)*15

# 储存棋盘格角点的世界坐标和图像坐标对
objpoints = [] # 在世界坐标系中的三维点
imgpoints = [] # 在图像平面的二维点

images = glob.glob('*.png')
gray = np.array([])
for fname in images:
    img = cv.imread(fname)
    gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)

    # 找到棋盘格角点
    ret, corners = cv.findChessboardCorners(gray, (w,h),None)

    # 如果找到足够点对，将其存储起来
    if ret == True:
        cv.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        objpoints.append(objp)
        imgpoints.append(corners)

        # 将角点在图像上显示
        cv.drawChessboardCorners(img, (w,h), corners, ret)
        #cv.imshow('findCorners',img)
        #cv.waitKey(0)

cv.destroyAllWindows()


# 标定
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
#print(type(rvecs),rvecs)
print(mtx, dist)
R = np.array([[1,0,0],
              [0,1,0],
              [0,0,1]])

T = np.array([[0,100,0]])

# rvec = cv.Rodrigues(cv.UMat(R.astype("float32")))
# tvec = cv.UMat(T.astype("float32"))

#rvec,jacbian = cv.Rodrigues(cv.UMat(R.astype("float32")))
rvec = np.array([[0,0,0]]).astype("float32")
tvec = T.astype("float32")

#read calibration from configure file
objectPoints = np.array([[50.0,100,3000]]) #objection 3D position


#transpose world axis 3D to plane axis 2D
imagePoints  = cv.projectPoints(objectPoints, rvec, tvec, mtx, dist)

point = imagePoints[0][0,0,:]
print(point)