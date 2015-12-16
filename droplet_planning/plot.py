import re

from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from svg_model.data_frame import close_paths


def get_path_colors(path_colors, df_connected):
    '''
    Determine polygon colors using `networkx` graph coloring algorithm.  This
    ensures that no two adjacent polygons are colored the same color.
    '''
    G = nx.Graph()
    G.add_edges_from(df_connected.values.tolist())
    color_map = pd.Series(nx.coloring.greedy_color(G, interchange=True))
    map_colors = path_colors[:color_map.max() + 1]
    return pd.Series(map_colors[color_map], index=color_map.index)


def plot_paths(df_paths, path_colors=None, labelsize=8, axis=None,
               draw_centers=False):
    '''
    Draw polygon paths from table of vertices (one row per vertex).

    Arguments
    ---------

     - `df_paths`: Table of polygon path vertices (one row per vertex).
         * Table rows with the same value in the `path_id` column are grouped
           together as a polygon.
    '''
    if axis is None:
        # Create blank axis to draw on.
        fig, axis = plt.subplots(figsize=(10, 10))
        axis.set_aspect(True)

    if path_colors is None:
        # Get reference to cycling color generator.
        colors = axis._get_lines.color_cycle

        # Assign a color to each path identifier.
        path_ids = df_paths.path_id.unique()
        path_colors = pd.Series([colors.next()
                                 for i in xrange(path_ids.shape[0])],
                                index=path_ids)

    # Draw electrode paths
    for path_id, path_i in close_paths(df_paths).groupby('path_id'):
        color = path_colors[path_id]
        #linewidth = 2
        #edge = Polygon(path_i[['x', 'y']].values, edgecolor=color, closed=True,
                       #linewidth=linewidth, facecolor='none')
        face = Polygon(path_i[['x', 'y']].values, edgecolor='none',
                       closed=True, facecolor=color, alpha=.45)
#         axis.add_patch(edge)
        axis.add_patch(face)

        # Set limits of axis view to device boundaries.
    axis.set_xlim(df_paths.x.min(), df_paths.x.max())
    axis.set_ylim(df_paths.y.min(), df_paths.y.max())

    path_centers = (df_paths[['path_id', 'x_center', 'y_center']]
                    .drop_duplicates())
    # Draw center of each electrode paths.
    if draw_centers:
        axis.scatter(path_centers.x_center, path_centers.y_center)
    if labelsize:
        for i, path_i in path_centers.iterrows():
            axis.text(path_i.x_center, path_i.y_center,
                      re.sub(r'[A-Za-z]*', '', path_i.path_id),
                      fontsize=labelsize)

    axis.set_xlabel('mm')
    axis.set_ylabel('mm')
    return axis


def draw_device(df_paths, df_connected, axis=None, **kwargs):
    '''
    Draw device using `networkx` graph coloring algorithm.  This ensures that
    no two adjacent polygons are colored the same color.
    '''
    if axis is None:
        # Create blank axis to draw on.
        fig, axis = plt.subplots(figsize=(18, 10))
        axis.set_aspect(True)

    # Get reference to cycling color generator.
    colors = axis._get_lines.color_cycle

    # Collect enough colors from matplotlib color cycle to color electrodes.
    colors_array = np.array([colors.next()
                             for i in xrange(10)])[[0, 1, 3, 5, 7]]

    # Use `networkx` graph coloring algorithm to color electrodes.
    # (Avoids using same color for adjacent electrodes).
    path_colors = get_path_colors(colors_array, df_connected[['source',
                                                              'destination']])
    plot_paths(df_paths, path_colors, axis=axis, **kwargs)
    #path_centers = df_paths[['x_center', 'y_center']].drop_duplicates()
    return axis


def draw_connections(df_paths, df_connected, color=None, axis=None):
    '''
    Draw the connections in the provided adjacency list.
    '''
    if axis is None:
        # Create blank axis to draw on.
        fig, axis = plt.subplots(figsize=(18, 10))
        axis.set_aspect(True)

    # Get reference to cycling color generator.
    colors = axis._get_lines.color_cycle

    #Draws the connections
    for index, row in df_connected.iterrows():
        path_current = df_paths[df_paths.path_id == row['source']]
        path_adjacent = df_paths[df_paths.path_id == row['destination']]

        path_current = path_current.append(path_adjacent)
        poly = Polygon(path_current[['x_center','y_center']].values,
                       edgecolor=colors.next() if color is None else color,
                       facecolor='none', alpha=.4, linewidth=5)
        axis.add_patch(poly)
    return axis


def draw_path(axis, df_indexed_path_centers, cycle, color='white'):
    '''
    Draw (closed) cycle of points.
    '''
    points = (df_indexed_path_centers.loc[list(cycle), ['x_center', 'y_center']])
    line = Line2D(points.x_center, points.y_center, color=color, linewidth=5)
    axis.add_line(line)

    x1, y1 = points.iloc[-1][['x_center', 'y_center']]
    x2, y2 = points.iloc[0][['x_center', 'y_center']]
    axis.arrow(x1, y1, x2 - x1, y2 - y1,
               head_width=0.5, head_length=0.5,
               fc='white', ec='white', linewidth=5)
