from Gcode_Parser import GcodeParser, Segment
import os
import math
import argparse
import logging

def increase_z_rect(model, z_raise_amt, x_min, x_max, y_min, y_max):
    for layer_index, layer in enumerate(model.layers):
        lines_iter = iter(enumerate(layer.lines))
        for line_index, line in lines_iter:
            if isinstance(line, Segment):
                if line.coords['X'] > x_min and line.coords['X'] < x_max \
                    and line.coords['Y'] > y_min and line.coords['Y'] < y_max:
                    new_z = line.coords['Z'] + z_raise_amt
                    line.coords['Z'] = round(new_z, 3)
                    absolute = {
                        "X": line.coords['X'],
                        "Y": line.coords['X'],
                        "Z": line.coords['Z'],
                        "F": line.coords["F"],  # no feedrate offset
                        "E": line.coords["E"]
                    }
                    new_line = "{0} X{1} Y{2} Z{3} E{4} F{5}".format(
                        line.type, line.coords['X'],
                        line.coords['Y'], line.coords['Z'],
                        line.coords['E'], line.coords["F"]
                    )
                    line.line = new_line

def increase_z_dome(model, z_raise_amt, x_centre, y_centre, radius):
    for layer_index, layer in enumerate(model.layers):
        lines_iter = iter(enumerate(layer.lines))
        for line_index, line in lines_iter:
            if isinstance(line, Segment):
                x_diff = (line.coords['X'] - x_centre) ** 2 
                y_diff = (line.coords['Y'] - y_centre) ** 2

                if x_diff + y_diff <= radius**2:
                    new_z = line.coords['Z'] + 1 / math.sqrt(x_diff + y_diff)
                    line.coords['Z'] = round(new_z, 3)
                    absolute = {
                        "X": line.coords['X'],
                        "Y": line.coords['X'],
                        "Z": line.coords['Z'],
                        "F": line.coords["F"],  # no feedrate offset
                        "E": line.coords["E"]
                    }
                    new_line = "{0} X{1} Y{2} Z{3} E{4} F{5}".format(
                        line.type, line.coords['X'],
                        line.coords['Y'], line.coords['Z'],
                        line.coords['E'], line.coords["F"]
                    )
                    line.line = new_line

def increase_z_circle(model, z_raise_amt, x_centre, y_centre, radius):
    for layer_index, layer in enumerate(model.layers):
        lines_iter = iter(enumerate(layer.lines))
        for line_index, line in lines_iter:
            if isinstance(line, Segment):
                x_diff = (line.coords['X'] - x_centre) ** 2 
                y_diff = (line.coords['Y'] - y_centre) ** 2
                if x_diff + y_diff <= radius**2:
                    new_z = line.coords['Z'] + z_raise_amt
                    line.coords['Z'] = round(new_z, 3)
                    absolute = {
                        "X": line.coords['X'],
                        "Y": line.coords['X'],
                        "Z": line.coords['Z'],
                        "F": line.coords["F"],  # no feedrate offset
                        "E": line.coords["E"]
                    }
                    new_line = "{0} X{1} Y{2} Z{3} E{4} F{5}".format(
                        line.type, line.coords['X'],
                        line.coords['Y'], line.coords['Z'],
                        line.coords['E'], line.coords["F"]
                    )
                    line.line = new_line

def main():
    parser = argparse.ArgumentParser(prog='select_z_raise.py',
                                     usage='%(prog)s [options]',
                                     description='Parses a G-code file \
                                                  into a custom object.')
    parser.add_argument(
        '-f', '--file',
        help='Path to the G-code file to be parsed.'
    )
    parser.add_argument(
        '-d', '--debug',
        help='Print lots of debugging statements.',
        action='store_const', dest='loglevel', const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help='Be verbose.',
        action='store_const', dest='loglevel', const=logging.INFO,
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    parser = GcodeParser()
    model = parser.parse_file(args.file)
    increase_z_rect(model, z_raise_amt=3.00, x_min=0, x_max=200, y_min=100, y_max=110)
    increase_z_dome(model, z_raise_amt=5.00, x_centre=117.5, y_centre=85.0, radius=10.0)
    increase_z_circle(model, z_raise_amt=10.00, x_centre=90, y_centre=65.0, radius=5.0)
    print(model)
    model.write("./test/select_z_raise_circle.gcode")

if __name__ == "__main__":
    main()