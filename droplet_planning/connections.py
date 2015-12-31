# coding: utf-8
# Copyright 2015
# Jerry Zhou <jerryzhou@hotmail.ca> and Christian Fobel <christian@fobel.net>
import pandas as pd
import numpy as np


def extend_paths(df, axis, distance):
    '''
    Extend polygon outline away from polygon center point by absolute distance.
    '''
    df_scaled = df.copy()
    offsets = df_scaled[axis + '_center_offset'].copy()
    offsets[offsets < 0] -= distance
    offsets[offsets >= 0] += distance
    df_scaled[axis] = df_scaled[axis + '_center'] + offsets
    return df_scaled


def extract_adjacent_paths(df_paths, extend=.5):
    '''
    Generate list of connections between "adjacent" polygon paths based on
    geometrical "closeness".

    Arguments
    ---------

     - `df_paths`: Table of polygon path vertices (one row per vertex).
         * Table rows with the same value in the `path_id` column are grouped
           together as a polygon.
    '''
    # Find corners of each solid path outline.
    df_scaled_x = extend_paths(df_paths, 'x', extend)  # Extend x coords by abs units
    df_scaled_y = extend_paths(df_paths, 'y', extend)  # Extend y coords by abs units

    df_corners = df_paths.groupby('path_id').agg({'x': ['min', 'max'],
                                                  'y': ['min', 'max'], })

    # Find adjacent electrodes
    row_list = []

    for pathNumber in df_paths['path_id'].drop_duplicates():
        df_stretched = df_scaled_x[df_scaled_x.path_id.isin([pathNumber])]
        xmin_x, xmax_x, ymin_x, ymax_x = (df_stretched.x.min(),
                                          df_stretched.x.max(),
                                          df_stretched.y.min(),
                                          df_stretched.y.max())
        df_stretched = df_scaled_y[df_scaled_y.path_id.isin([pathNumber])]
        xmin_y, xmax_y, ymin_y, ymax_y = (df_stretched.x.min(),
                                          df_stretched.x.max(),
                                          df_stretched.y.min(),
                                          df_stretched.y.max())

        #Some conditions unnecessary if it is assumed that electrodes don't overlap
        adjacent = df_corners[
            ((df_corners.x['min'] < xmax_x) & (df_corners.x['max'] >= xmax_x)
            # Check in x stretched direction
            |(df_corners.x['min'] < xmin_x) & (df_corners.x['max'] >= xmin_x))
            # Check if y is within bounds
            & (df_corners.y['min'] < ymax_x) & (df_corners.y['max'] > ymin_x) |

            #maybe do ymax_x - df_corners.y['min'] > threshold &
            #  df_corners.y['max'] - ymin_x > threshold

            ((df_corners.y['min'] < ymax_y) & (df_corners.y['max'] >= ymax_y)
             # Checks in y stretched direction
             |(df_corners.y['min'] < ymin_y) & (df_corners.y['max'] >= ymin_y))
             # Check if x in within bounds
            & ((df_corners.x['min'] < xmax_y) & (df_corners.x['max'] > xmin_y))
        ].index.values

        for path in adjacent:
            temp_dict = {}
            reverse_dict = {}

            temp_dict ['source'] = pathNumber
            reverse_dict['source'] = path
            temp_dict ['target'] = path
            reverse_dict['target'] = pathNumber

            if(reverse_dict not in row_list):
                row_list.append(temp_dict)

    df_connected = (pd.DataFrame(row_list)[['source', 'target']]
                    .sort(axis=1, ascending=False).sort(['source', 'target']))
    return df_connected


def get_adjacency_matrix(df_connected):
    '''
    Return matrix where $a_{i,j} = 1$ indicates polygon $i$ is connected to
    polygon $j$.

    Also, return mapping (and reverse mapping) from original keys in
    `df_connected` to zero-based integer index used for matrix rows and
    columns.
    '''
    sorted_path_keys = np.sort(np.unique(df_connected[['source', 'target']]
                                         .values.ravel()))
    indexed_paths = pd.Series(sorted_path_keys)
    path_indexes = pd.Series(indexed_paths.index, index=sorted_path_keys)

    adjacency_matrix = np.zeros((path_indexes.shape[0], ) * 2, dtype=int)
    for i_key, j_key in df_connected[['source', 'target']].values:
        i, j = path_indexes.loc[[i_key, j_key]]
        adjacency_matrix[i, j] = 1
        adjacency_matrix[j, i] = 1
    return adjacency_matrix, indexed_paths, path_indexes
