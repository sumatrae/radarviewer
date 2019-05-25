import numpy as np
mtx = np.array([[1.14016483e+03, 0.00000000e+00, 3.24629743e+02],
         [0.00000000e+00, 1.11387327e+03, 3.94472576e+02],
         [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
dist = np.array([ 0.00931659,  0.12528377, -0.00095163,  0.00264823, -0.36374799])

R = np.array([[1,0,0],
              [0,1,0],
              [0,0,1]])

T = np.array([[0,100,0]])


rvec = np.array([[0,100,0]]).astype("float32")
tvec = T.astype("float32")

#read calibration from configure file
objectPoints = np.array([[3000.0,-1200,6000]]) #objection 3D position