import os
import logging
import argparse
import time
from Gcode_Parser import GcodeParser
from conform_surface import increase_z
from line_splitter import convert_to_small_segments
from point_cloud import extract_point_cloud, convert_to_number, convert_to_list, coord_write

def main():
    parser = argparse.ArgumentParser(
        prog="select_z_raise.py",
        usage="%(prog)s [options]",
        description="Parses a G-code file into a custom object.",
    )
    parser.add_argument(
        "-f",
        "--file",
        default="test/conform/test_rect_absolute.gcode",
        help="Path to the G-code file to be parsed and conformed.",
    )
    parser.add_argument(
        "-s",
        "--surface",
        default="test/conform/dome.gcode",
        help="Path to the G-code file of substrate/surface ",
    )
    parser.add_argument(
        "-l",
        "--length",
        help="Maximum length of a single line.",
        type=float,
        default=1.00,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Print lots of debugging statements.",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.ERROR,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Be verbose.",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.ERROR)

    in_file, _ = os.path.splitext(os.path.basename(args.file))
    pointcloud_path = os.path.join(
        os.path.dirname(args.file),
        "pointcloud_{}_{}.txt".format(args.length, in_file),
    )
    # check if the point cloud has already been generated
    if not os.path.exists(pointcloud_path):
        # generate the point cloud
        print("Generating point cloud file...")
        t1 = time.time()
        parser = GcodeParser()
        model = parser.parse_file(args.surface)
        model = convert_to_small_segments(model, args.length / 2) # split into 1mm units
        coordinates = extract_point_cloud(model)
        coordinates = convert_to_number(coordinates)
        coordinates = convert_to_list(coordinates)
        coord_write(coordinates, pointcloud_path) # changed output file path
        t2 = time.time()
        print("Extracted point cloud in {:.3f} ms".format((t2 - t1) * 1000.0))
    else:
        print("Point cloud file already exists...")

    print("Reading in point cloud...")
    with open(pointcloud_path) as f:
        surface = f.read().splitlines()

    splitted_path = os.path.join(
        os.path.dirname(args.file),
        "conformed_{}_{}.gcode".format(args.length, in_file),
    )

    conformed_path = os.path.join(
        os.path.dirname(args.file),
        "conformed_{}_{}.gcode".format(args.length, in_file),
    )
    t1 = time.time()
    parser = GcodeParser()
    model = parser.parse_file(args.file)
    print()
    print("Model information before conforming:")
    print(model)
    print()
    print("Conforming print to point cloud surface...")
    model = increase_z(model, surface, args.length)
    model.write(conformed_path) # changed file path for saving output
    t2 = time.time()
    print("Conformed in {:.3f} ms".format((t2 - t1) * 1000.0))
    parser = GcodeParser()
    model = parser.parse_file(conformed_path)
    print()
    print("Model information after conforming:")
    print(model)
    print()

if __name__ == "__main__":
    main()
