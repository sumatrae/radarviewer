import matplotlib.pyplot  as plt
import numpy as np
import matplotlib.animation as antt

fig = plt.figure()

img = fig.add_subplot(111)

a, = img.plot(np.random.rand(36), 'green')


def dtt(data):
    a.set_ydata(data)

    return a,


def dong():
    while True:
        yield np.random.rand(36)


gif = antt.FuncAnimation(fig, func = dtt, init_func = dong, interval=1000)

plt.show()