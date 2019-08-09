######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains classes for handling project item execution.

:author: P. Savolainen (VTT)
:date:   8.4.2019
"""

import logging
import os
import fnmatch
from PySide2.QtCore import Signal, Slot, QObject
import networkx as nx


class DirectedGraphHandler:
    """Class for manipulating graphs according to user's actions.

    Args:
        toolbox (ToolboxUI): QMainWindow instance
    """

    def __init__(self, toolbox):
        """Class constructor."""
        self._toolbox = toolbox
        self.running_dag = None
        self.running_item = None
        self._dags = list()

    def dags(self):
        """Returns a list of graphs (DiGraph) in the project."""
        return self._dags

    def add_dag(self, dag):
        """Add graph to list.

        Args:
            dag (DiGraph): Graph to add
        """
        self._dags.append(dag)

    def remove_dag(self, dag):
        """Remove graph from instance variable list.

        Args:
            dag (DiGraph): Graph to remove
        """
        self._dags.remove(dag)

    def add_dag_node(self, node_name):
        """Create directed graph with one node and add it to list.

        Args:
            node_name (str): Project item name to add as a node
        """
        dag = nx.DiGraph()
        dag.add_node(node_name)
        self._dags.append(dag)

    def add_graph_edge(self, src_node, dst_node):
        """Adds an edge between the src and dst nodes. If nodes are in
        different graphs, the reference to union graph is saved and the
        references to the original graphs are removed. If src and dst
        nodes are already in the same graph, the edge is added to the graph.
        If src and dst are the same node, a self-loop (feedback) edge is
        added.

        Args:
            src_node (str): Source project item node name
            dst_node (str): Destination project item node name
        """
        src_graph = self.dag_with_node(src_node)
        dst_graph = self.dag_with_node(dst_node)
        if src_node == dst_node:
            # Add self-loop to src graph and return
            src_graph.add_edge(src_node, dst_node)
            return
        if src_graph == dst_graph:
            # src and dst are already in same graph. Just add edge to src_graph and return
            src_graph.add_edge(src_node, dst_node)
            return
        # Unify graphs
        union_dag = nx.union(src_graph, dst_graph)
        union_dag.add_edge(src_node, dst_node)
        self.add_dag(union_dag)
        # Remove src and dst graphs
        self.remove_dag(src_graph)
        self.remove_dag(dst_graph)
        return

    def remove_graph_edge(self, src_node, dst_node):
        """Removes edge from a directed graph.

        Args:
            src_node (str): Source project item node name
            dst_node (str): Destination project item node name
        """
        dag = self.dag_with_edge(src_node, dst_node)
        if src_node == dst_node:  # Removing self-loop
            dag.remove_edge(src_node, dst_node)
            return
        # dag_copy = copy.deepcopy(dag)  # Make a copy before messing with the graph
        dag.remove_edge(src_node, dst_node)
        # Check if src or dst node is isolated (without connections) after removing the edge
        if self.node_is_isolated(src_node):
            dag.remove_node(src_node)  # Remove node from original dag
            g = nx.DiGraph()
            g.add_node(src_node)  # Make a new graph containing only the isolated node
            self.add_dag(g)
            return
        if self.node_is_isolated(dst_node):
            dag.remove_node(dst_node)
            g = nx.DiGraph()
            g.add_node(dst_node)
            self.add_dag(g)
            return
        # If src node still has a path (ignoring edge directions) to dst node -> return, we're fine
        if self.nodes_connected(dag, src_node, dst_node):
            return
        # Now for the fun part. We need to break the original DAG into two separate DAGs.
        # Get src node descendant edges, ancestor edges, and its own edges
        src_descendants = nx.descendants(dag, src_node)
        src_descendant_edges = nx.edges(dag, src_descendants)
        src_ancestors = nx.ancestors(dag, src_node)
        src_ancestor_edges = nx.edges(dag, src_ancestors)
        src_edges = nx.edges(dag, src_node)
        # Get dst node descendant edges, ancestor edges, and its own edges
        dst_descendants = nx.descendants(dag, dst_node)
        dst_descendant_edges = nx.edges(dag, dst_descendants)
        dst_ancestors = nx.ancestors(dag, dst_node)
        dst_ancestor_edges = nx.edges(dag, dst_ancestors)
        dst_edges = nx.edges(dag, dst_node)
        # Make descendant graph. This graph contains src node and all its neighbors.
        descendant_graph = nx.DiGraph()
        descendant_graph.add_edges_from(src_descendant_edges)
        descendant_graph.add_edges_from(src_ancestor_edges)
        descendant_graph.add_edges_from(src_edges)
        # Make ancestor graph. This graph contains the dst node and all its neighbors.
        ancestor_graph = nx.DiGraph()
        ancestor_graph.add_edges_from(dst_descendant_edges)
        ancestor_graph.add_edges_from(dst_ancestor_edges)
        ancestor_graph.add_edges_from(dst_edges)
        # Remove old graph and add new graphs instead
        self.remove_dag(dag)
        self.add_dag(descendant_graph)
        self.add_dag(ancestor_graph)

    def remove_node_from_graph(self, node_name):
        """Removes node from a graph that contains
        it. Called when project item is removed from project.

        Args:
            node_name (str): Project item name
        """
        # This is called every time a previous project is closed and another is opened.
        g = self.dag_with_node(node_name)
        edges_to_remove = list()
        for edge in g.edges():
            if node_name in (edge[0], edge[1]):
                edges_to_remove.append(edge)
        g.remove_edges_from(edges_to_remove)
        # Now remove the node itself
        g.remove_node(node_name)
        # Loop through remaining nodes and check if any of them are isolated now
        nodes_to_remove = list()
        for node in g.nodes():
            if self.node_is_isolated(node, allow_self_loop=True):
                nodes_to_remove.append(node)
                h = nx.DiGraph()
                h.add_node(node)
                if g.has_edge(node, node):
                    h.add_edge(node, node)
                self.add_dag(h)
        g.remove_nodes_from(nodes_to_remove)
        if not g.nodes():
            self.remove_dag(g)

    def rename_node(self, old_name, new_name):
        """Handles renaming the node and edges in a graph when a project item is renamed.

        Args:
            old_name (str): Old project item name
            new_name (str): New project item name

        Returns:
            bool: True if successful, False if renaming failed
        """
        g = self.dag_with_node(old_name)
        mapping = {old_name: new_name}  # old_name->new_name
        nx.relabel_nodes(g, mapping, copy=False)  # copy=False modifies g in place

    def dag_with_node(self, node_name):
        """Returns directed graph that contains given node.

        Args:
            node_name (str): Node to look for

        Returns:
            (DiGraph): Directed graph that contains node or None if not found.
        """
        for dag in self.dags():
            if dag.has_node(node_name):
                return dag
        logging.error("Graph containing node %s not found. Something is wrong.", node_name)
        return None

    def dag_with_edge(self, src_node, dst_node):
        """Returns directed graph that contains given edge.

        Args:
            src_node (str): Source node name
            dst_node (str): Destination node name

        Returns:
            (DiGraph): Directed graph that contains edge or None if not found.
        """
        for dag in self.dags():
            if dag.has_edge(src_node, dst_node):
                return dag
        logging.error("Graph containing edge %s->%s not found. Something is wrong.", src_node, dst_node)
        return None

    def calc_exec_order(self, g):
        """Returns an bfs-ordered list of nodes in the given graph.
        Adds a dummy source node to the graph if there are more than
        one nodes that have no inbound connections. The dummy source
        node is needed for the bfs-algorithm.

        Args:
            g (DiGraph): Directed graph to process

        Returns:
            list: bfs-ordered list of node names (first item at index 0).
            Empty list if given graph is not a DAG.
        """
        exec_order = list()
        if not nx.is_directed_acyclic_graph(g):
            return exec_order
        sources = self.source_nodes(g)  # Project items that have no inbound connections
        if not sources:
            # Should not happen if nx.is_directed_acyclic_graph() works
            logging.error("This graph has no source nodes. Execution failed.")
            return exec_order
        if len(sources) > 1:
            # Make an invisible source node for all nodes that have no inbound connections
            invisible_src_node = 0  # This is unique name since it's an integer. Item called "0" can still be created
            g.add_node(invisible_src_node)
            for src in sources:
                g.add_edge(invisible_src_node, src)
            # Calculate bfs-order by using the invisible dummy source node
            edges_to_execute = list(nx.bfs_edges(g, invisible_src_node))
            # Now remove the invisible dummy source node
            for src in sources:
                g.remove_edge(invisible_src_node, src)
            g.remove_node(invisible_src_node)
        else:
            # The dag contains only one source item, so it can be used as the source node directly
            # Calculate bfs-order
            edges_to_execute = list(nx.bfs_edges(g, sources[0]))
            exec_order.append(sources[0])  # Add source node
        # Collect dst nodes from bfs-edge iterator
        for src, dst in edges_to_execute:
            exec_order.append(dst)
        return exec_order

    def node_is_isolated(self, node, allow_self_loop=False):
        """Checks if the project item with the given name has any connections.

        Args:
            node (str): Project item name
            allow_self_loop (bool): If default (False), Self-loops are considered as an
                in-neighbor or an out-neighbor so the method returns False. If True,
                single node with a self-loop is considered isolated.

        Returns:
            bool: True if project item has no in-neighbors nor out-neighbors, False if it does.
                Single node with a self-loop is NOT isolated (returns False).
        """
        g = self.dag_with_node(node)
        if not allow_self_loop:
            return nx.is_isolate(g, node)
        has_self_loop = g.has_edge(node, node)
        if not has_self_loop:
            return nx.is_isolate(g, node)
        # The node has a self-loop.
        # Node degree is the number of edges that are connected to it. A self-loop increases the degree by 2
        deg = g.degree(node)
        if deg - 2 == 0:  # If degree - 2 is zero, it is isolated.
            return True
        return False

    @staticmethod
    def source_nodes(g):
        """Returns a list of source nodes in given graph.
        A source node has no incoming edges. This is determined
        by calculating the in-degree of each node in the graph.
        If nodes in-degree == 0, it is a source node

        Args:
            g (DiGraph): Graph to examine

        Returns:
            list: List of source node names or an empty list is there are none.
        """
        s = list()
        for node in g.nodes():
            in_deg = g.in_degree(node)
            if in_deg == 0:
                # logging.debug("node:{0} is a source node".format(node))
                s.append(node)
        return s

    @staticmethod
    def nodes_connected(dag, a, b):
        """Checks if node a is connected to node b. Edge directions are ignored.
        If any of source node a's ancestors or descendants have a path to destination
        node b, returns True. Also returns True if destination node b has a path to
        any of source node a's ancestors or descendants.

        Args:
            dag (DiGraph): Graph that contains nodes a and b
            a (str): Node name
            b (str): Another node name

        Returns:
            bool: True if a and b are connected, False otherwise
        """
        src_anc = nx.ancestors(dag, a)
        src_des = nx.descendants(dag, a)
        # logging.debug("src {0} ancestors:{1}. descendants:{2}".format(a, src_anc, src_des))
        # Check ancestors
        for anc in src_anc:
            # Check if any src ancestor has a path to dst node
            if nx.has_path(dag, anc, b):
                # logging.debug("Found path from anc {0} to dst {1}".format(anc, b))
                return True
            # Check if dst node has a path to any src ancestor
            if nx.has_path(dag, b, anc):
                # logging.debug("Found path from dst {0} to anc {1}".format(b, anc))
                return True
        # Check descendants
        for des in src_des:
            # Check if any src descendant has a path to dst node
            if nx.has_path(dag, des, b):
                # logging.debug("Found path from des {0} to dst {1}".format(des, b))
                return True
            # Check if dst node has a path to any src descendant
            if nx.has_path(dag, b, des):
                # logging.debug("Found path from dst {0} to des {1}".format(b, des))
                return True
        return False

    @staticmethod
    def export_to_graphml(g, path):
        """Export given graph to a path in GraphML format.

        Args:
            g (DiGraph): Graph to export
            path (str): Full output path for GraphML file

        Returns:
            bool: Operation success status
        """
        if not nx.is_directed_acyclic_graph(g):
            return False
        nx.write_graphml(g, path, prettyprint=True)
        return True


class ExecutionInstance(QObject):
    """Class for the graph that is being executed. Contains references to
    files and resources advertised by project items so that project items downstream can find them.

    Args:
        toolbox (ToolboxUI): QMainWindow instance
        execution_list (list): Ordered list of nodes to execute
    """

    graph_execution_finished_signal = Signal(int, name="graph_execution_finished_signal")
    project_item_execution_finished_signal = Signal(int, name="project_item_execution_finished_signal")

    def __init__(self, toolbox, execution_list):
        """Class constructor."""
        QObject.__init__(self)
        self._toolbox = toolbox
        self.execution_list = execution_list  # Ordered list of nodes to execute. First node at index 0
        self.running_item = None
        self.dc_refs = list()  # Data Connection reference list
        self.dc_files = list()  # Data Connection file list
        self.ds_refs = dict()  # DS refs. Key is dialect, value is a list of paths or urls depending on dialect
        self.di_data = dict()  # Data Interface data. Key is DI name, value is data for import
        self.tool_output_files = list()  # Paths to result files from ToolInstance

    def start_execution(self):
        """Pops the next item from the execution list and starts executing it."""
        self.running_item = self.execution_list.pop(0)
        self.execute_project_item()

    def execute_project_item(self):
        """Starts executing project item."""
        self.project_item_execution_finished_signal.connect(self.item_execution_finished)
        item_ind = self._toolbox.project_item_model.find_item(self.running_item)
        item = self._toolbox.project_item_model.project_item(item_ind)
        item.execute()

    @Slot(int, name="item_execution_finished")
    def item_execution_finished(self, item_finish_state):
        """Pop next project item to execute or finish current graph if there are no items left.

        Args:
            item_finish_state (int): 0=Continue to next project item. -2=Stop executing this graph (happens when e.g.
            Tool does not find req. input files or something)
        """
        self.project_item_execution_finished_signal.disconnect()
        if item_finish_state == -1:
            # Item execution failed due to e.g. Tool did not find input files or something
            self.graph_execution_finished_signal.emit(-1)
            return
        if item_finish_state == -2:
            # User pressed Stop button
            self.graph_execution_finished_signal.emit(-2)
            return
        try:
            self.running_item = self.execution_list.pop(0)
        except IndexError:
            self.graph_execution_finished_signal.emit(0)
            return
        self.execute_project_item()

    def stop(self):
        """Stops running project item and terminates current graph execution."""
        if not self.running_item:
            self._toolbox.msg.emit("No running item")
            self.graph_execution_finished_signal.emit(-2)
            return
        item_ind = self._toolbox.project_item_model.find_item(self.running_item)
        item = self._toolbox.project_item_model.project_item(item_ind)
        item.stop_execution()
        return

    def add_ds_ref(self, dialect, ref):
        """Adds given database reference to a dictionary. Key is the dialect.
        If dialect is sqlite, value is a list of full paths to sqlite files.
        For other dialects, key is the dialect and value is a list of URLs to
        database servers.

        Args:
            dialect (str): Dialect name (lower case)
            ref (str): Database reference
        """
        try:
            self.ds_refs[dialect].append(ref)
        except KeyError:
            self.ds_refs[dialect] = [ref]

    def add_di_data(self, di_name, data):
        """Adds given data from data interface to a list.

        Args:
            di_name (str): Data interface name
            data (dict): Data to import
        """
        self.di_data[di_name] = data

    def append_dc_refs(self, refs):
        """Adds given file paths (Data Connection file references) to a list.

        Args:
            refs (list): List of file paths (references)
        """
        self.dc_refs += refs

    def append_dc_files(self, files):
        """Adds given project data file paths to a list.

        Args:
            files (list): List of file paths
        """
        self.dc_files += files

    def append_tool_output_file(self, filepath):
        """Adds given file path to a list containing paths to Tool output files.

        Args:
            filepath (str): Path to a tool output file (in tool result directory)
        """
        self.tool_output_files.append(filepath)

    def find_file(self, filename):
        """Returns the first occurrence to full path to given file name or None if file was not found.

        Args:
            filename (str): Searched file name (no path) TODO: Change to pattern

        Returns:
            str: Full path to file if found, None if not found
        """
        # Look in Data Stores
        # SQLITE
        try:
            for sqlite_ref in self.ds_refs["sqlite"]:
                _, file_candidate = os.path.split(sqlite_ref)
                if file_candidate == filename:
                    # logging.debug("Found path for {0} from ds refs: {1}".format(filename, sqlite_ref))
                    return sqlite_ref
        except KeyError:
            pass
        # MYSQL
        try:
            for mysql_url in self.ds_refs["mysql"]:
                _, file_candidate = os.path.split(mysql_url)
                if file_candidate == filename:
                    # logging.debug("Found path for {0} from ds refs: {1}".format(filename, mysql_url))
                    return mysql_url
        except KeyError:
            pass
        # MSSQL
        try:
            for mssql_url in self.ds_refs["mssql"]:
                _, file_candidate = os.path.split(mssql_url)
                if file_candidate == filename:
                    # logging.debug("Found path for {0} from ds refs: {1}".format(filename, mssql_url))
                    return mssql_url
        except KeyError:
            pass
        # POSTGRESQL
        try:
            for postgresql_url in self.ds_refs["postgresql"]:
                _, file_candidate = os.path.split(postgresql_url)
                if file_candidate == filename:
                    # logging.debug("Found path for {0} from ds refs: {1}".format(filename, postgresql_url))
                    return postgresql_url
        except KeyError:
            pass
        # ORACLE
        try:
            for oracle_url in self.ds_refs["oracle"]:
                _, file_candidate = os.path.split(oracle_url)
                if file_candidate == filename:
                    logging.debug("Found path for % from ds refs: %s", filename, oracle_url)
                    return oracle_url
        except KeyError:
            pass
        # Look in Data Connections
        for dc_ref in self.dc_refs:
            _, file_candidate = os.path.split(dc_ref)
            if file_candidate == filename:
                # logging.debug("Found path for {0} from dc refs: {1}".format(filename, dc_ref))
                return dc_ref
        for dc_file in self.dc_files:
            _, file_candidate = os.path.split(dc_file)
            if file_candidate == filename:
                # logging.debug("Found path for {0} from dc files: {1}".format(filename, dc_file))
                return dc_file
        # Look in Tool output files
        for tool_file in self.tool_output_files:
            _, file_candidate = os.path.split(tool_file)
            if file_candidate == filename:
                # logging.debug("Found path for {0} from Tool result files: {1}".format(filename, tool_file))
                return tool_file
        return None

    def find_optional_files(self, pattern):
        """Returns a list of found paths to files that match the given pattern.

        Returns:
            list: List of (full) paths
        """
        # logging.debug("Searching optional input files. Pattern: '{0}'".format(pattern))
        matches = list()
        # Find matches when pattern includes wildcards
        if ('*' in pattern) or ('?' in pattern):
            # Find matches in Data Store references
            try:
                # NOTE: Only sqlite files are checked
                ds_matches = fnmatch.filter(self.ds_refs["sqlite"], pattern)
            except KeyError:
                ds_matches = list()
            # Find matches in Data Connection references
            dc_ref_matches = fnmatch.filter(self.dc_refs, pattern)
            # Find matches in Data Connection data files
            dc_file_matches = fnmatch.filter(self.dc_files, pattern)
            # Find matches in Tool output files
            tool_matches = fnmatch.filter(self.tool_output_files, pattern)
            matches += ds_matches + dc_ref_matches + dc_file_matches + tool_matches
        else:
            # Pattern is an exact filename (no wildcards)
            match = self.find_file(pattern)
            if match is not None:
                matches.append(match)
        # logging.debug("Matches:{0}".format(matches))
        return matches