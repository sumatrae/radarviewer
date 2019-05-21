import cv2 as cv
import numpy as np


rotate_R = np.array([[1,0,0],
                     [0,1,0],
                     [0,0,1]])
y_offset = 100 #100 mm
transpose_T = np.array([0,y_offset,0])


rvec = cv.Rodrigues(rotate_R)
tvec = transpose_T


#read calibration from configure file
objectPoints = [1,2,3] #objection 3D position
cameraMatrix, distCoeffs = [1],[1]


#transpose world axis 3D to plane axis 2D
imagePoints  = cv.projectPoints(objectPoints, rvec, tvec, cameraMatrix, distCoeffs)