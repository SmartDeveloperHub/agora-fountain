"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org

  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2015 Center for Open Middleware.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

__author__ = 'Fernando Serena'


import networkx as nx


def compare_path_graphs(test, pattern):
    """

    :param test:
    :param pattern:
    :return:
    """
    if len(test) == len(pattern):
        for expected in pattern:
            try:
                valid_graph = filter(lambda x: x == expected, test).pop()
                test.remove(valid_graph)
            except IndexError:
                pass
        return not len(test)
    return False


class AgoraGraph(nx.DiGraph):
    def __init__(self, data=None, **attr):
        super(AgoraGraph, self).__init__(data, **attr)

    @property
    def types(self):
        """

        :return:
        """
        return [t for t, data in self.nodes(data=True) if data['ty'] == 'type']

    @property
    def properties(self):
        """

        :return:
        """
        return [t for t, data in self.nodes(data=True) if data['ty'] == 'prop']

    def _check_node_type(self, f, ty):
        """

        :param f:
        :param ty:
        :return:
        """
        def wrapper(name):
            for n, data in self.nodes_iter(data=True):
                if n == name:
                    if data['ty'] == ty:
                        return f(name)
                    raise Exception(ty)
            raise KeyError(ty)

        return wrapper

    def get_type_properties(self, ty):
        """

        :param ty:
        :return:
        """
        return self._check_node_type(self.successors, 'type')(ty)

    def get_type_refs(self, ty):
        """

        :param ty:
        :return:
        """
        return self._check_node_type(self.predecessors, 'type')(ty)

    def get_property_domain(self, prop):
        """

        :param prop:
        :return:
        """
        return self._check_node_type(self.predecessors, 'prop')(prop)

    def get_property_range(self, prop):
        """

        :param prop:
        :return:
        """
        return self._check_node_type(self.successors, 'prop')(prop)

    def get_inverse_property(self, prop):
        """

        :param prop:
        :return:
        """
        cycles = list(nx.simple_cycles(self.copy()))
        for cycle in cycles:
            if prop in cycle and len(cycle) == 4:
                p_index = cycle.index(prop)
                return cycle[p_index - 2]
        return None

    def add_types_from(self, types):
        """

        :param types:
        :return:
        """
        for ty in types:
            self.add_node(ty, ty='type', label=ty)

    def add_type(self, ty):
        """

        :param ty:
        :return:
        """
        self.add_node(ty, ty='type', label=ty)

    def add_properties_from(self, props, obj=True):
        """

        :param props:
        :param obj:
        :return:
        """
        for prop in props:
            self.add_node(prop, ty='prop', object=obj, label=prop)

    def add_property(self, prop, obj=True):
        """

        :param prop:
        :param obj:
        :return:
        """
        self.add_node(prop, ty='prop', object=obj, label=prop)

    def link_types(self, source, link, dest):
        """

        :param source:
        :param link:
        :param dest:
        :return:
        """
        self.add_edges_from([(source, link), (link, dest)])

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        def match(x, y):
            return x == y

        return nx.is_isomorphic(self, other, node_match=match, edge_match=match)


class PathGraph(AgoraGraph):
    def __init__(self, path=None, cycles=None, data=None, **attr):
        super(PathGraph, self).__init__(data, **attr)
        self.__seeds = set([])
        self.__cycle_graphs = {}
        self.__cycle_ids = []
        self.__prev_type, self.__prev_prop = None, None
        self.root = None
        if type(path) is dict:
            self.__parse_path(path)
        if type(cycles) is list:
            self.__parse_cycles(cycles)

    def __parse_path(self, path):
        """

        :param path:
        :return:
        """
        path_seeds = path['seeds']
        if path_seeds:
            self.__seeds = set(path_seeds)
        raw_steps = path['steps']
        self.__cycle_ids = path.get('cycles', [])

        for step in raw_steps:
            ty, prop = step['type'], step['property']
            self.add_step(ty, prop)

    def __parse_cycles(self, cycles):
        """

        :param cycles:
        :return:
        """
        for cycle in cycles:
            cid = cycle['cycle']
            if cid in self.__cycle_ids:
                cycle_steps = cycle['steps']
                cycle_graph = CycleGraph()
                for step in cycle_steps:
                    ty, prop = step['type'], step['property']
                    cycle_graph.add_step(ty, prop)
                self.__cycle_graphs[cid] = cycle_graph

    def add_step(self, ty, prop):
        """

        :param ty:
        :param prop:
        :return:
        """
        self.add_type(ty)
        self.add_property(prop)
        if self.__prev_prop is not None:
            self.add_edge(self.__prev_prop, ty)
        self.add_edge(ty, prop)
        self.__prev_type, self.__prev_prop = ty, prop
        if self.root is None:
            self.root = ty

    @property
    def seeds(self):
        """

        :return:
        """
        return self.__seeds

    @property
    def cycles(self):
        """

        :return:
        """
        return self.__cycle_graphs.keys()

    def get_cycle(self, cid):
        """

        :param cid:
        :return:
        """
        return self.__cycle_graphs[cid]

    def set_cycle(self, cid, graph):
        """

        :param cid:
        :param graph:
        :return:
        """
        self.__cycle_graphs[cid] = graph

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        def node_match(a_attr, b_attr):
            return a_attr == b_attr

        def edge_match(a_attr, b_attr):
            return a_attr == b_attr

        def compare_cycles():
            def match_cycle(cid):
                cycle = self.get_cycle(cid)
                for o_cid in other.cycles:
                    o_cycle = other.get_cycle(o_cid)
                    if cycle == o_cycle:
                        return True
                return False

            if len(self.cycles) == len(other.cycles):
                return len(self.cycles) == len(filter(match_cycle, self.cycles))
            return False

        return self.seeds == other.seeds and nx.is_isomorphic(self, other, node_match=node_match,
                                                              edge_match=edge_match) and compare_cycles()


class CycleGraph(PathGraph):
    def __init__(self, path=None, cycles=None, data=None, **attr):
        super(CycleGraph, self).__init__(path=path, cycles=cycles, data=data, **attr)
        self.__cycle_edge_prop = None

    def add_step(self, ty, prop):
        """

        :param ty:
        :param prop:
        :return:
        """
        super(CycleGraph, self).add_step(ty, prop)
        if self.__cycle_edge_prop is not None:
            self.remove_edge(self.__cycle_edge_prop, self.root)
        self.add_edge(prop, self.root)
        self.__cycle_edge_prop = prop