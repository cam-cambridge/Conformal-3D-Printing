from Gcode_Parser import GcodeParser, Segment
import os
import math
import argparse
import logging
from line_splitter import convert_to_small_segments
import time
from point_cloud import convert_to_number
from tqdm import tqdm

class NotRelativeExtrusion(ValueError):
    pass


def coord_is_valid(line, coord, max_seg_length):
    if abs(line.coords["X"] - coord[0]) < (max_seg_length * 0.5) and abs(
        line.coords["Y"] - coord[1]
    ) < (max_seg_length * 0.5):
        return True
    return False


def increase_z(model, surface_coords, max_seg_length):
    e_diff = 0
    model = convert_to_small_segments(model, max_seg_length)
    surface_coords = convert_to_number(surface_coords)

    lines = [
        line
        for layer in model.layers
        for line in layer.lines
        if isinstance(line, Segment)
    ]

    for line_idx, line in tqdm(enumerate(lines), total=len(lines)):
        if "G92 E0" in line.line:
            e_running = 0
        z = [
            coord[2]
            for coord in surface_coords
            if abs(line.coords["X"] - coord[0]) < (max_seg_length * 0.5)
            and abs(line.coords["Y"] - coord[1]) < (max_seg_length * 0.5)
        ]
        z = z if z else [0]
        if z:
            z_max = max(z)
            if z_max:
                epsilon = 0.2
                line.coords["Z"] = max(z) + line.coords["Z"] + epsilon
            z_diff = abs(lines[line_idx - 1].coords["Z"] - line.coords["Z"])
            if line.coords.get("E") and lines[line_idx - 1].coords.get("E") and (z_max or z_diff):
                if line_idx > 0:
                    x_diff = abs(lines[line_idx - 1].coords["X"] - line.coords["X"])
                    y_diff = abs(lines[line_idx - 1].coords["Y"] - line.coords["Y"])
                    z_diff = abs(lines[line_idx - 1].coords["Z"] - line.coords["Z"])
                    distance = math.sqrt((x_diff ** 2) + (y_diff ** 2))
                    if distance > 0: # new segment to if function to prevent zero error. 
                        factor = math.sqrt((distance ** 2) + (z_diff ** 2)) / distance
                        line.coords["E"] = line.coords["E"] + e_running
                        e_diff = abs(lines[line_idx - 1].coords["E"] - line.coords["E"])
                        new_e = lines[line_idx - 1].coords["E"] + (e_diff * factor)
                        e_running = e_running + (new_e - line.coords["E"])
                        line.coords["E"] = new_e
                
                if line.type == "G1":
                    line.line = "{0} X{1} Y{2} Z{3} E{4} F{5}".format(
                        line.type,
                        line.coords["X"],
                        line.coords["Y"],
                        line.coords["Z"],
                        line.coords["E"],
                        line.coords["F"],
                    )
            else:
                if line.type == "G1":
                    if line.coords.get("E") and "E" in line.line:
                        line.coords["E"] += e_running
                        line.line = "{0} X{1} Y{2} Z{3} E{4} F{5}".format(
                            line.type,
                            line.coords["X"],
                            line.coords["Y"],
                            line.coords["Z"],
                            line.coords["E"],
                            line.coords["F"],
                        )
                    else:
                        line.line = "{0} X{1} Y{2} Z{3} F{4}".format(
                            line.type,
                            line.coords["X"],
                            line.coords["Y"],
                            line.coords["Z"],
                            line.coords["F"],
                        )
                
    return model


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
        help="Path to the G-code file to be parsed.",
    )
    parser.add_argument(
        "-s",
        "--surface",
        default="test/conform/extracted_dome.txt",
        help="Path to the extracted point cloud of conformal surface.",
    )
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
    t1 = time.time()
    parser = GcodeParser()
    model = parser.parse_file(args.file)

    with open(args.surface) as f:
        surface = f.read().splitlines()

    bed_centre = [117.5, 117.5] # The centre of a (235, 235) bed found on Creality printers
    model = increase_z(model, surface, bed_centre, 1)
    in_file, _ = os.path.splitext(os.path.basename(args.file))
    model.write("test/raised_{}.gcode".format(in_file)) #changed file path for saving output
    t2 = time.time()
    print("Completed in: {:.3f} ms".format((t2 - t1) * 1000.0))


if __name__ == "__main__":
    main()
