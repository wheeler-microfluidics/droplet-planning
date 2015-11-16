# coding: utf-8
import re

import networkx as nx
import pandas as pd
import pint  # Unit conversion from inches to mm
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
from svg_model.svgload import svg_parser
from svg_model.data_frame import (get_svg_frame, close_paths, get_nearest_neighbours,
                                  get_path_areas, get_bounding_boxes, get_path_infos,
                                  get_bounding_box)


# Convert Inkscape pixels-per-inch (PPI) to pixels-per-mm (PPmm).
ureg = pint.UnitRegistry()

INKSCAPE_PPI = 90
INKSCAPE_PPmm = INKSCAPE_PPI / ureg.inch.to('mm')


def get_paths_frame_with_centers(df_paths):
    '''
    Compute the center point of each polygon path, and the offset of each vertex to the corresponding polygon center point.

    Arguments
    ---------

     - `df_paths`: Table of polygon path vertices (one row per vertex).
         * Table rows with the same value in the `path_id` column are grouped
           together as a polygon.
    '''
    df_paths = df_paths.copy()
    # Get coordinates of center of each path.
    df_paths_info = get_path_infos(df_paths)
    path_centers = df_paths_info[['x', 'y']] + .5 * df_paths_info[['width', 'height']].values
    df_paths['x_center'] = path_centers.x[df_paths.path_id].values
    df_paths['y_center'] = path_centers.y[df_paths.path_id].values

    # Calculate coordinate of each path vertex relative to center point of path.
    center_offset = df_paths[['x', 'y']] - df_paths[['x_center', 'y_center']].values
    return df_paths.join(center_offset, rsuffix='_center_offset')


def get_scaled_svg_frame(svg_filepath, scale=INKSCAPE_PPmm.magnitude):
    # Read device layout from SVG file.
    df_device = get_svg_frame(svg_filepath)

    # Offset device, such that all coordinates are >= 0.
    df_device[['x', 'y']] -= df_device[['x', 'y']].min()

    # Scale path coordinates based on Inkscape default of 90 pixels-per-inch.
    df_device[['x', 'y']] /= INKSCAPE_PPmm.magnitude

    df_paths = get_paths_frame_with_centers(df_device)
    return df_paths
