import matplotlib.pyplot as plt
import numpy as np
from Gcode_Parser import GcodeParser, Segment
from point_cloud import convert_to_number
from plot_config import *
import os
import logging
logging.basicConfig(level=logging.ERROR)

def plot_point_cloud(path):
    with open(path) as f:
        pc = f.read().splitlines()    
    pc = np.array(convert_to_number(pc))
    X, Y, Z = pc[:, 0], pc[:, 1], pc[:, 2]
    fig = plt.figure(figsize=[6,6], dpi=300)
    ax = fig.add_subplot(projection='3d')
    ax.scatter(X, Y, Z, s=1, marker=".", alpha=0.5, color=colors[4])
    ax.axes.set_xlim3d(left=95, right=140)
    ax.axes.set_ylim3d(bottom=95, top=140)
    ax.axes.set_zlim3d(bottom=0, top=45)

    # Create cubic bounding box to simulate equal aspect ratio
    max_range = np.array([X.max() - X.min(), Y.max() - Y.min(), Z.max() - Z.min()]).max()
    Yb = 0.5 * max_range * np.mgrid[-1:2:2,-1:2:2,-1:2:2][1].flatten() + 0.5 * (Y.max() + Y.min())
    Xb = 0.5 * max_range * np.mgrid[-1:2:2,-1:2:2,-1:2:2][0].flatten() + 0.5 * (X.max() + X.min())
    Zb = 0.5 * max_range * np.mgrid[-1:2:2,-1:2:2,-1:2:2][2].flatten() + 0.5 * (Z.max() + Z.min())
    # Add the fake bounding box for make scaling correct:
    for xb, yb, zb in zip(Xb, Yb, Zb):
        ax.plot([xb], [yb], [zb], 'w')

    elev, azim = 10, 70
    ax.view_init(elev, azim)
    print('ax.azim {}'.format(ax.azim))
    print('ax.elev {}'.format(ax.elev))
    fig.savefig("plots/pc.jpg", dpi=300)

def plot_gcode(path, scatter=False):
    parser = GcodeParser()
    model = parser.parse_file(path)
    lines = [
        line
        for layer in model.layers
        for line in layer.lines
        if isinstance(line, Segment)
    ]

    fig = plt.figure(figsize=[6,6], dpi=300)
    ax = fig.add_subplot(projection='3d')

    X, Y, Z = [], [], []
    for line in lines:
        if line.coords["E"]>0:
            # print(line.line)
            X.append(line.coords["X"])
            Y.append(line.coords["Y"])
            Z.append(line.coords["Z"])
    
    if scatter:
        type = "scatter"
        ax.scatter(X, Y, Z, s=1, marker=".", alpha=0.5, color=colors[4])
    else:
        type = "line"
        ax.plot(X, Y, Z, color=colors[4])

    ax.axes.set_xlim3d(left=75, right=160)
    ax.axes.set_ylim3d(bottom=75, top=160)
    ax.axes.set_zlim3d(bottom=0, top=100)

    elev, azim = 20, 70
    ax.view_init(elev, azim)
    print('ax.azim {}'.format(ax.azim))
    print('ax.elev {}'.format(ax.elev))
    filename = os.path.splitext(os.path.basename(path))[0]
    fig.savefig(f"plots/{filename}_{type}.jpg", dpi=300)

if __name__ == "__main__":
    # plot_point_cloud("test/conform/pointcloud_test_rect_absolute.txt")
    # plot_gcode("test/conform/dome.gcode", scatter=False)
    # plot_gcode("test/conform/test_rect_absolute.gcode", scatter=True)
    # plot_gcode('/mnt/d/CAM_Git/camgp/src/test/conform/conformed_1.0_test_rect_absolute.gcode', scatter=False)
    path = "test\conform\conformed_1.0_Thin_film.gcode"
    plot_gcode(path)