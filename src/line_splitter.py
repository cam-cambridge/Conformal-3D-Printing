import math
import argparse
import logging
import time
import os
from itertools import islice
from Gcode_Parser import GcodeParser, Segment


def split_segments(model, seg_current, seg_previous, max_seg_length):
    number_of_segs = math.ceil(seg_current.distance / max_seg_length)
    new_segs = []
    for i in range(1, number_of_segs):
        k = i / number_of_segs
        x1 = seg_previous.coords["X"]
        y1 = seg_previous.coords["Y"]
        z1 = seg_previous.coords["Z"]
        x2 = seg_current.coords["X"]
        y2 = seg_current.coords["Y"]
        z2 = seg_current.coords["Z"]

        e1 = seg_previous.coords["E"]
        e2 = seg_current.coords["E"]

        new_x, new_y, new_z = x1 + k * (x2 - x1), y1 + k * (y2 - y1), z1 + k * (z2 - z1)

        new_x = round(new_x, 3)
        new_y = round(new_y, 3)
        new_z = round(new_z, 3)

        new_coords = {
            "X": new_x,
            "Y": new_y,
            "Z": new_z,
            "F": seg_current.coords["F"],  # no feedrate offset
        }

        if e1 == e2 and not model.relative_extrusion:
            line = "{0} X{1} Y{2} Z{3} F{4}".format(
                seg_current.type, new_x, new_y, new_z, seg_current.coords["F"]
            )

        else:
            if model.relative_extrusion:
                new_e = k * e2
            else:
                new_e = e1 + k * (e2 - e1)
            new_e = round(new_e, 3)
            new_coords["E"] = round(new_e, 3)

            if "E" in seg_current.line:
                line = "{0} X{1} Y{2} Z{3} E{4} F{5}".format(
                    seg_current.type, new_x, new_y, new_z, new_e, seg_current.coords["F"]
                )
            else:
                line = "{0} X{1} Y{2} Z{3} F{4}".format(
                    seg_current.type, new_x, new_y, new_z, seg_current.coords["F"]
                )

        seg = Segment(seg_current.type, new_coords, seg_current.line_num, line)
        seg.distance = seg_current.distance / number_of_segs
        new_segs.append(seg)
    return new_segs


class Found(Exception):
    pass


class Halt(Exception):
    pass


def check_halt(line):
    if "EXTRUDING_STOP" in line.line[0:14]:
        raise Halt


def convert_to_small_segments(model, max_seg_length=10):
    line = None
    previous_line = None
    try:
        for layer_idx, layer in enumerate(model.layers):
            lines_iter = iter(enumerate(layer.lines))
            for line_idx, line in lines_iter:
                check_halt(line)
                if isinstance(line, Segment) and line.distance > max_seg_length:
                    if line_idx > 0:
                        previous_line = layer.lines[line_idx - 1]
                    else:
                        if layer_idx > 0:
                            try:
                                for i in range(1, layer_idx):
                                    for j in range(
                                        1, len(model.layers[layer_idx - i].lines)
                                    ):
                                        previous_line = model.layers[
                                            layer_idx - i
                                        ].lines[-j]
                                        if isinstance(previous_line, Segment):
                                            raise Found
                            except Found:
                                pass

                    if isinstance(previous_line, Segment):
                        new_segs = split_segments(
                            model, line, previous_line, max_seg_length
                        )
                        for i in range(len(new_segs)):
                            layer.lines.insert(line_idx + i, new_segs[i])
                        next(islice(lines_iter, len(new_segs) - 1, None), "")
    except Halt:
        pass
    return model


def split_directory(dir_path, seg_len=1):
    logging.basicConfig(level=logging.ERROR)
    for gcode in os.listdir(os.path.join(dir_path, "original")):
        t1 = time.time()
        gcode_path = os.path.join(dir_path, "original", gcode)
        in_file, ext = os.path.splitext(os.path.basename(gcode_path))
        if ext == ".gcode":
            parser = GcodeParser()
            model = parser.parse_file(gcode_path)
            in_file, _ = os.path.splitext(os.path.basename(gcode_path))
            model = convert_to_small_segments(model, seg_len)
            model.write(
                os.path.join(
                    dir_path, "split", "split_{}mm_{}.gcode".format(seg_len, in_file)
                )
            )
            t2 = time.time()
            print("Completed in: {:.3f} ms".format((t2 - t1) * 1000.0))
            print(model)


def main():
    parser = argparse.ArgumentParser(
        prog="gcode_parser.py",
        usage="%(prog)s [options]",
        description="Parses a G-code file into a custom object.",
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
        "-l",
        "--length",
        help="Maximum length of a single line.",
        type=float,
        default=5.00,
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
    t1 = time.time()
    parser = GcodeParser()
    model = parser.parse_file(args.file)
    print(model)
    in_file, _ = os.path.splitext(os.path.basename(args.file))
    model = convert_to_small_segments(model, args.length)
    split_path = os.path.join(
        os.path.dirname(args.file),
        "split_{}mm_{}.gcode".format(args.length, in_file),
    )
    model.write(split_path)
    t2 = time.time()
    print("Completed in: {:.3f} ms".format((t2 - t1) * 1000.0))
    
    parser = GcodeParser()
    model = parser.parse_file(split_path)
    print(model)


if __name__ == "__main__":
    main()

