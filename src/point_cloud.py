import argparse
import logging
from Gcode_Parser import GcodeParser, Segment
from line_splitter import convert_to_small_segments
import os


def extract_point_cloud(model):
    coordinates = []
    lines = [line for layer in model.layers for line in layer.lines]
    for seg in lines:
        if isinstance(seg, Segment) and seg.coords.get("E", 0) > 0:
            coordinate = "{0} {1} {2}".format(
                seg.coords["X"], seg.coords["Y"], seg.coords["Z"]
            )  # return a string
            coordinates.append(coordinate)
    return coordinates


def create_coord(coordinate):
    bit = coordinate.split(" ", 2)
    coord = [float(bit[0]), float(bit[1]), float(bit[2])]
    return coord


def convert_to_number(coordinates):
    coords = [create_coord(coordinate) for coordinate in coordinates]
    return coords


def find_centre(coords):
    coord_x = [coord[0] for coord in coords]
    coord_y = [coord[1] for coord in coords]

    x_centre = ((max(coord_x) + min(coord_x))) / 2
    y_centre = ((max(coord_y) + min(coord_y))) / 2
    centre = [x_centre, y_centre]
    return centre


def convert_to_list(coords):
    coords = ["{0} {1} {2}".format(coord[0], coord[1], coord[2]) for coord in coords]
    return coords


def coord_write(coordinates, file_path):
    with open(file_path, "w+") as fp:
        for coordinate in coordinates:
            coordinate = str(coordinate)
            fp.write(coordinate)
            fp.write("\n")


def main():
    parser = argparse.ArgumentParser(
        prog="Coordinates.py",
        usage="%(prog)s [options]",
        description="Parses a G-code file \
                                                  into a custom object.",
    )
    parser.add_argument("-f", "--file", help="Path to the G-code file to be parsed.")
    parser.add_argument(
        "-d",
        "--debug",
        help="Print lots of debugging statements.",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
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
    logging.basicConfig(level=args.loglevel)
    parser = GcodeParser()

    model = parser.parse_file(args.file)

    for layer in model.layers:
        for line in layer.lines:
            print(line)

    model = convert_to_small_segments(model, 1)
    for layer in model.layers:
        for line in layer.lines:
            print(line)
            
    coordinates = extract_point_cloud(model)
    coordinates = convert_to_number(coordinates)
    centre = find_centre(coordinates)
    coordinates = convert_to_list(coordinates)
    in_file, _ = os.path.splitext(os.path.basename(args.file))
    coord_write(coordinates, "test/extracted_{}.txt".format(in_file)) #changed output file path


if __name__ == "__main__":
    main()
