import networkx as nx
from .connections import extract_adjacent_paths, get_adjacency_matrix


def svg_polygons_to_channels(svg_source, xpath='svg:polygon',
                             namespaces=None):
    '''
    `svg_source`: A file path, URI, or file-like object.
    '''
    from lxml import etree
    import pandas as pd

    XHTML_NAMESPACE = "http://www.w3.org/2000/svg"
    NSMAP = {'svg' : XHTML_NAMESPACE}  # map default namespace to prefix 'svg:'

    if namespaces is None:
        namespaces = NSMAP

    e_root = etree.parse(svg_source)
    return (pd.DataFrame([[polygon_i.attrib['id'],
                           map(int, polygon_i.attrib
                               .get('data-channels', '')
                               .split(','))]
                          for polygon_i in
                          e_root.xpath(xpath, namespaces=NSMAP)],
                         columns=['id', 'channels'])
            .set_index('id')['channels'])


# Extract [adjacency list][1] from paths data frame.
#
# [1]: https://en.wikipedia.org/wiki/Adjacency_list
class DeviceFrames(object):
    def __init__(self, svg_source, **kwargs):
        from svg_model import svg_polygons_to_df, compute_shape_centers

        extend = kwargs.pop('extend', .5)
        self.electrode_channels = svg_polygons_to_channels(svg_source,
                                                           **kwargs)
        # Read device layout from SVG file.
        df_device = svg_polygons_to_df(svg_source)
        #self.df_paths = scale_svg_frame(df_device)
        self.df_paths = compute_shape_centers(df_device, 'path_id')
        self.df_connected = extract_adjacent_paths(self.df_paths, extend)
        self.df_connected['cost'] = 1

        # The following returns one row per electrode, indexed by electrode path id
        self.df_path_centers = (self.df_paths.drop_duplicates(['path_id'])
                                .set_index('path_id')[['x_center',
                                                       'y_center']])
        (self.adjacency_matrix, self.indexed_paths,
         self.path_indexes) = get_adjacency_matrix(self.df_connected)
        self.df_indexed_path_centers = (self.df_path_centers
                                        .loc[self.path_indexes.index]
                                        .reset_index())
        self.df_indexed_path_centers.rename(columns={'index': 'path_id'},
                                            inplace=True)

        self.df_connected_indexed = self.df_connected.copy()
        self.df_connected_indexed['source'] = map(str, self.path_indexes
                                                  [self.df_connected
                                                   ['source']])
        self.df_connected_indexed['target'] = map(str, self.path_indexes
                                                       [self.df_connected
                                                        ['target']])

        self.df_paths_indexed = self.df_paths.copy()
        self.df_paths_indexed['path_id'] = map(str, self.path_indexes
                                               [self.df_paths.path_id])
        self.graph = nx.Graph()
        for index, row in self.df_connected.iterrows():
            self.graph.add_edge(row['source'], row['target'],
                                cost=row['cost'])

    # Returns a list of nodes on the shortest path from source to target.
    def find_path(self, source_id, target_id):
        if source_id == target_id:
            shortest_path = [source_id]
        else:
            shortest_path = nx.dijkstra_path(self.graph, source_id, target_id,
                                             'cost')
        return shortest_path
