import math
import argparse
import logging
import time
from itertools import islice
import os

try:
    import numpy as np
except:
    print("Can run without Numpy but will be slower")

class GcodeParser:
    """
    Parses a G-code file into a custom G-code model object
    """

    def __init__(self):
        """Initalisation of the GCODE model"""
        self.model = GcodeModel(parser=self)
        self.line_num = 0
        self.line = None

    def parse_file(self, path):
        """
        Opens and reads the GCODE file
        incrementing a line counter,
        removing trailing linefeed and
        parsing the line.
        """
        with open(path, "r") as f:
            self.line_num = 0
            for line in f:
                self.line_num += 1
                self.line = line.rstrip()
                self.parse_line()

        self.model.post_process()
        return self.model

    def parse_line(self):
        """
        Strips comments and extracts
        the clean command.
        """
        bits = self.line.split(";", 1)
        if len(bits) > 1 and bits[0] == "":
            comment = bits[1]
            self.parse_comment(comment)
            logging.info("Comment: %s", comment)

        command = bits[0].strip()

        # TODO: strip logical line number and checksum

        comm = command.split(None, 1)
        code = comm[0] if (len(comm) > 0) else None
        args = comm[1] if (len(comm) > 1) else None
        comment = comment = bits[1] if len(bits) > 1 else None

        if code:
            if hasattr(self, "parse_" + code):
                getattr(self, "parse_" + code)(args)
            elif code == "M117":
                self.parse_M117(args)
            else:
                self.parse_misc(args)
                self.warn("Unknown code '{}'".format(code))

    def parse_args(self, args):
        """
        Parses the arguments for G-code
        """
        dic = {}
        if args:
            bits = args.split()
            for bit in bits:
                letter = bit[0]
                try:
                    coord = float(bit[1:])
                    dic[letter] = coord
                except ValueError as e:
                    self.warn("Invalid line provided, {}".format(bits))
        return dic

    def parse_comment(self, comment):
        """ """
        self.model.add_comment(comment)

    def parse_G0(self, args):
        """
        GO - rapid move, same as G1 for 3D printers
        """
        self.parse_G1(args, "G0")

    def parse_G1(self, args, type="G1"):
        """
        G1 - controlled move
        """
        self.model.do_G1(self.parse_args(args), type)

    def parse_G20(self, args):
        """
        G20 - set units to inches
        """
        self.error("Unsupported & incompatible: G20: Set Units to Inches")

    def parse_G21(self, args):
        """
        G21 - set units to mm
        default nothing to do so pass
        """
        self.model.do_G21(self.parse_args(args))

    def parse_G28(self, args):
        """
        G28 - move to origin
        """
        self.model.do_G28(self.parse_args(args))

    def parse_G29(self, args):
        """
        G29 - bed levelling
        """
        self.model.do_G29(self.parse_args(args))

    def parse_G90(self, args):
        """
        G90 - set absolute positioning
        """
        self.model.do_G90(self.parse_args(args))

    def parse_G91(self, args):
        """
        G91 - set relative positioning
        """
        self.model.do_G91(self.parse_args(args))

    def parse_G92(self, args):
        """
        G92 - set position
        """
        self.model.do_G92(self.parse_args(args))

    def parse_M82(self, args):
        """
        M82 - general M command
        """
        self.model.do_M82(self.parse_args(args))

    def parse_M83(self, args):
        """
        M83 - relative extrusion
        """
        self.model.do_M83(self.parse_args(args))

    def parse_M104(self, args):
        """
        M104 - general M command
        """
        self.model.do_M104(self.parse_args(args))

    def parse_M106(self, args):
        """
        M106 - general M command
        """
        self.model.do_M106(self.parse_args(args))

    def parse_M109(self, args):
        """
        M109 - general M command
        """
        self.model.do_M109(self.parse_args(args))

    def parse_M117(self, args):
        """
        M117 - general M command
        """
        self.model.do_M117(args)

    def parse_M140(self, args):
        """
        M140 - general M command
        """
        self.model.do_M140(self.parse_args(args))

    def parse_M190(self, args):
        """
        M190 - general M command
        """
        self.model.do_M190(self.parse_args(args))

    def parse_misc(self, args):
        self.model.do_misc(self.parse_args(args))

    def warn(self, msg):
        """
        Log a warning message if debug is true
        """
        logging.warning("Line %d: %s (Text: %s)", self.line_num, msg, self.line)

    def error(self, msg):
        """
        Log an error message if debug is true
        """
        logging.error("Line %d: %s (Text: %s)", self.line_num, msg, self.line)
        raise Exception(
            "[ERROR] Line {0}: {1} (Text:'{2}')".format(self.line_num, msg, self.line)
        )


class BBox:
    def __init__(self, coords):
        self.xmin = self.xmax = coords["X"]
        self.ymin = self.ymax = coords["Y"]
        self.zmin = self.zmax = coords["Z"]

    def dx(self):
        return self.xmax - self.xmin

    def dy(self):
        return self.ymax - self.ymin

    def dz(self):
        return self.zmax - self.zmin

    def cx(self):
        return (self.xmax + self.xmin) / 2

    def cy(self):
        return (self.ymax + self.ymin) / 2

    def cz(self):
        return (self.zmax + self.zmin) / 2

    def extend(self, coords):
        self.xmin = min(self.xmin, coords["X"])
        self.xmax = max(self.xmax, coords["X"])
        self.ymin = min(self.ymin, coords["Y"])
        self.ymax = max(self.ymax, coords["Y"])
        self.zmin = min(self.zmin, coords["Z"])
        self.zmax = max(self.zmax, coords["Z"])

    def __str__(self):
        return "X: {}, {}; Y: {} {}; Z: {} {};".format(
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.zmin,
            self.zmax,
        )


class GcodeModel:
    def __init__(self, parser):
        # save parser for messages
        self.parser = parser
        # latest coordinates & extrusion relative to offset, feedrate
        self.relative = {"X": 0.0, "Y": 0.0, "Z": 0.0, "F": 0.0, "E": 0.0}
        # offsets for relative coordinates and position reset (G92)
        self.offset = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0}

        # if true, args for move (G1) are given relatively (default: absolute)
        self.is_relative = False
        # the segments
        self.segments = []
        self.layers = None
        self.distance = None
        self.extrudate = None
        self.bbox = None

        self.relative_extrusion = False

    def write(self, file_path):
        with open(file_path, "w+") as fp:
            for layer in self.layers:
                for segment in layer.lines:
                    fp.write(segment.line)
                    fp.write("\n")

    def add_comment(self, _comment):
        """ """
        comment = Line(";", self.parser.line_num, self.parser.line, _comment)
        self.add_segment(comment)

    def do_G1(self, args, type):
        """
        G0/G1: Rapid/Controlled move
        """
        # clone previous coords
        coords = dict(self.relative)
        # update changed coords
        for axis in list(args.keys()):
            if axis in coords:
                if self.is_relative:
                    if axis != "F" or axis != "E":
                        coords[axis] += args[axis]
                    else:
                        if self.relative_extrusion and axis == "E":
                            coords[axis] += args[axis]
                        else:
                            coords[axis] = args[axis]
                else:
                    if self.relative_extrusion and axis == "E":
                        coords[axis] += args[axis]
                    else:
                        coords[axis] = args[axis]
            else:
                self.warn("Unknown axis '{}'".format(axis))
        # build segment
        absolute = {
            "X": self.offset["X"] + coords["X"],
            "Y": self.offset["Y"] + coords["Y"],
            "Z": self.offset["Z"] + coords["Z"],
            "F": coords["F"],  # no feedrate offset
            "E": self.offset["E"] + coords["E"],
        }
        seg = Segment(type, absolute, self.parser.line_num, self.parser.line)
        self.add_segment(seg)
        # update model coords
        self.relative = coords

    def do_G21(self, args):
        """
        G21: set units to millimeters
        Does nothing as can't handle inches really
        """
        line = Line("G21", self.parser.line_num, self.parser.line)
        self.add_segment(line)

    def do_G28(self, args):
        """
        G28: Move to Origin.
        TODO: Implement moving to the origin
        """
        if not len(list(args.keys())):
            args = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        # update specified axes
        for axis in list(args.keys()):
            if axis in self.offset:
                # transfer value from relative to offset
                self.offset[axis] = args[axis]
                self.relative[axis] = args[axis]
            else:
                self.warn("Unknown axis '{}'".format(axis))
        line = Segment("G28", self.relative, self.parser.line_num, self.parser.line)
        self.add_segment(line)

    def do_G29(self, args):
        """
        G29: Bed Levelling
        TODO: N/A
        """
        line = Line("G29", self.parser.line_num, self.parser.line)
        self.add_segment(line)

    def do_G90(self, args):
        line = Line("G90", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.set_relative(False)

    def do_G91(self, args):
        line = Line("G91", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.set_relative(True)

    def do_G92(self, args):
        """
        G92: Set Position this changes the current coords,
        without moving, so do not generate a segment.
        """
        # no axes mentioned == all axes to 0
        if not len(list(args.keys())):
            args = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0}
        # update specified axes
        for axis in list(args.keys()):
            if axis in self.offset:
                # transfer value from relative to offset
                self.offset[axis] = args[axis]
                self.relative[axis] = args[axis]
            else:
                self.warn("Unknown axis '{}'".format(axis))
        line = Segment("G92", self.relative, self.parser.line_num, self.parser.line)
        self.add_segment(line)

    def do_M82(self, args):
        self.relative_extrusion = False
        line = Line("M82", self.parser.line_num, self.parser.line)
        self.add_segment(line)

    def do_M83(self, args):
        self.relative_extrusion = True
        line = Line("M83", self.parser.line_num, self.parser.line)
        self.add_segment(line)

    def do_M104(self, args):
        line = Line("M104", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.warn("M104 unimplemented")

    def do_M106(self, args):
        line = Line("M106", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.warn("M106 unimplemented")

    def do_M109(self, args):
        line = Line("M109", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.warn("M109 unimplemented")

    def do_M117(self, args):
        line = Line("M117", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.warn("M117 unimplemented")

    def do_M140(self, args):
        line = Line("M140", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.warn("M140 unimplemented")

    def do_M190(self, args):
        line = Line("M190", self.parser.line_num, self.parser.line)
        self.add_segment(line)
        self.warn("M190 unimplemented")

    def do_misc(self, args):
        line = Line("MISC", self.parser.line_num, self.parser.line)
        self.add_segment(line)

    def set_relative(self, is_relative):
        """
        Sets the boolean value is_relative.
        If true, args for move (G1) are given relatively
        If false move is absolute (default)

        Parameters::
                is_relative - boolean for absolute or relative movement
        """
        self.is_relative = is_relative

    def add_segment(self, segment):
        """
        Adds a segment to the list of
        current segments

        Parameters::
                segment - the segment to be added
        """
        self.segments.append(segment)

    def insert_segment(self, index, segment):
        self.segments.insert(index, segment)

    def warn(self, msg):
        """
        Parser warning message

        Parameters::
                msg - the warning message
        """
        self.parser.warn(msg)

    def error(self, msg):
        """
        Parser error message

        Parameters::
                msg - the error message
        """
        self.parser.error(msg)

    def classify_segments(self):
        """
        Applies intelligence (rough rules of thumb ;) )
        to classify segments.
        """

        # start model at 0
        coords = {"X": 0.0, "Y": 0.0, "Z": 0.0, "F": 0.0, "E": 0.0}

        # first layer at Z=0
        current_layer_idx = 0
        currentLayerZ = 0

        for seg in self.segments:
            if not isinstance(seg, Segment):
                continue

            # default style is fly (move, no extrusion)
            style = "fly"

            # no horizontal movement, but extruder movement: retraction/refill
            if (
                (seg.coords["X"] == coords["X"])
                and (seg.coords["Y"] == coords["Y"])
                and (seg.coords["E"] != coords["E"])
            ):
                style = "retract" if (seg.coords["E"] < coords["E"]) else "restore"

            # some horizontal movement, and positive extruder movement: extrusion
            if (
                (seg.coords["X"] != coords["X"])
                or (seg.coords["Y"] != coords["Y"])
                and (seg.coords["E"] > coords["E"])
            ):
                style = "extrude"

            # positive extruder movement in a different Z signals a layer change for this segment
            if (seg.coords["E"] > coords["E"]) and (seg.coords["Z"] != currentLayerZ):
                currentLayerZ = seg.coords["Z"]
                current_layer_idx += 1

            # set style and layer in segment
            seg.style = style
            seg.layer_idx = current_layer_idx

            # execute segment
            coords = seg.coords

    def split_layers(self):
        """
        Splits the segments into previously detected layers.
        Layers detected with a Z change.
        """

        # start model at 0
        coords = {"X": 0.0, "Y": 0.0, "Z": 0.0, "F": 0.0, "E": 0.0}

        # init layer store
        self.layers = []

        current_layer_idx = -1

        # for all segments
        for seg in self.segments:
            # next layer
            if current_layer_idx != seg.layer_idx:
                layer = Layer(coords["Z"])
                layer.start = coords
                self.layers.append(layer)
                current_layer_idx = seg.layer_idx

            layer.lines.append(seg)

            # execute segment
            if isinstance(seg, Segment):
                coords = seg.coords

        self.topLayer = len(self.layers) - 1

    def calc_metrics(self):
        """
        Various metrics of the model are calculated.
        (not necessary)
        """

        # init distances and extrudate
        self.distance = 0
        self.extrudate = 0

        # init model bbox
        self.bbox = None

        # extender helper
        def extend(bbox, coords):
            if bbox is None:
                return BBox(coords)
            else:
                bbox.extend(coords)
                return bbox

        # for all layers
        for layer in self.layers:
            # start at layer start
            coords = layer.start

            # init distances and extrudate
            layer.distance = 0
            layer.extrudate = 0

            # include start point
            self.bbox = extend(self.bbox, coords)

            # for all segments
            for line in layer.lines:

                if not isinstance(line, Segment):
                    continue

                # calc XYZ distance
                d = (line.coords["X"] - coords["X"]) ** 2
                d += (line.coords["Y"] - coords["Y"]) ** 2
                d += (line.coords["Z"] - coords["Z"]) ** 2
                line.distance = math.sqrt(d)

                # calc extrudate
                if line.style == "extrude":
                    diff = line.coords["E"] - coords["E"]
                    line.extrudate = diff if diff > 0 else 0
                else:
                    line.extrudate = 0

                # accumulate layer metrics
                layer.distance += line.distance
                layer.extrudate += line.extrudate

                # execute segment
                coords = line.coords

                # include end point
                extend(self.bbox, coords)

            # accumulate total metrics
            self.distance += layer.distance
            self.extrudate += layer.extrudate

    def post_process(self):
        self.classify_segments()
        self.split_layers()
        self.calc_metrics()

    def __str__(self):
        return "<GcodeModel: len(segments)={0}, len(layers)={1}, distance={2}mm, extrudate={3}mm, bbox={4}>".format(
            len(self.segments),
            len(self.layers),
            round(self.distance, 4),
            round(self.extrudate, 4),
            self.bbox,
        )


class Line:
    """
    Class for a line of GCODE
    can be comment, moves, heating etc
    """

    def __init__(self, type, line_num, line, comment=None):
        self.type = type
        self.line_num = line_num
        self.line = line
        self.style = None
        self.layer_idx = None
        self.comment = comment.strip() if comment else None

    def __str__(self):
        return "<Line: type={0}, line_num={1}, style={2}, layer_idx={3}, comment={4}, line={5}>".format(
            self.type,
            self.line_num,
            self.style,
            self.layer_idx,
            self.comment,
            self.line,
        )


class Segment(Line):
    """
    Class for a segment of GCODE
    can be fly, extrude, retract, restore
    """

    def __init__(self, type, coords, line_num, line):
        super().__init__(type, line_num, line)
        self.coords = coords
        self.distance = None
        self.extrudate = None

    def __str__(self):
        return "<Segment: type={0}, line_num={1}, style={2}, layer_idx={3}, distance={4}, extrudate={5}, line={6}>".format(
            self.type,
            self.line_num,
            self.style,
            self.layer_idx,
            self.distance,
            self.extrudate,
            self.line,
        )


class Layer:
    """
    Class for a layer of GCODE
    (same Z coord, differing X and Y)
    """

    def __init__(self, Z):
        self.Z = Z
        self.lines = []
        self.distance = None
        self.extrudate = None

    def __str__(self):
        return "<Layer: Z={0}, len(lines)={1}, distance={2}, extrudate={3}>".format(
            self.Z, len(self.lines), self.distance, self.extrudate
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="gcode_parser.py",
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
    logging.basicConfig(level=logging.ERROR)
    t1 = time.time()
    parser = GcodeParser()
    model = parser.parse_file(args.file)
    filename, ext = os.path.splitext(os.path.basename(args.file))
    dirname = os.path.dirname(args.file)
    filename = filename + "_parsed" + ext
    model.write(os.path.join(dirname, filename))
    t2 = time.time()
    print("Completed in: {:.3f} ms".format((t2 - t1) * 1000.0))
    print(model)
