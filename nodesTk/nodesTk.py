#!/usr/bin/python3

import argparse
import datetime
import json
import re
import urllib.request
from typing import Union


class Network:
    def __init__(self):
        self.nodes_dict = dict()  # node_id as key and Node obj as value
        self.links_dict = dict()  # node_ids alphabetically concatenated as key and Link obj as value
        self.tiers_dict = dict()  # tier number as key and set of node_id as value
        self.tier_nodes_set = set()  # a set of all node_id who already have a tier

        # A set of node IDs that are known to be VPN only (e.g. supernodes).
        # Use this if the VPN flags in your graph.json are known to be incorrect.
        self.vpn_only_nodes = set()

    def add_link(self, newlink):
        link = [newlink.source, newlink.target]
        link.sort(key=str.lower)
        self.links_dict["-".join(link)] = newlink  # now with 'Streckenstrich'(tm)

    def add_node(self, node):
        self.nodes_dict[node.node_id] = node
        if node.is_gateway:
            self.add_node_to_tier(node.node_id, 0)

    def get_node(self, node_id):
        return self.nodes_dict[node_id]

    def add_node_to_tier(self, node_id, tier):
        if node_id in self.tier_nodes_set:
            return
        if tier not in self.tiers_dict:
            self.tiers_dict[tier] = set()
        self.tiers_dict[tier].add(node_id)
        self.tier_nodes_set.add(node_id)

    def get_neighbours_of_node(self, node_id, vpn_neighbours=False):
        return self.get_neighbours_of_node_find_fake_meshes(node_id, vpn_neighbours)[0]

    def get_neighbours_of_node_find_fake_meshes(self, node_id, vpn_neighbours=False):
        fake_mesh_connections = set()
        if not self.nodes_dict[node_id].mesh_neighbours_set or not self.nodes_dict[node_id].vpn_neighbours_set:
            self.nodes_dict[node_id].mesh_neighbours_set = set()
            self.nodes_dict[node_id].vpn_neighbours_set = set()
            for link_id in self.links_dict:
                other_node_id = None
                if self.links_dict[link_id].source == node_id:
                    other_node_id = self.links_dict[link_id].target
                elif self.links_dict[link_id].target == node_id:
                    other_node_id = self.links_dict[link_id].source

                if other_node_id:
                    if self.links_dict[link_id].vpn:
                        self.nodes_dict[node_id].vpn_neighbours_set.add(other_node_id)
                    elif node_id in self.vpn_only_nodes or other_node_id in self.vpn_only_nodes:
                        # This connection is marked as non-VPN but one of the nodes is a known VPN only host.
                        # Therefore this must be a VPN connection.
                        fake_mesh_connections.add(frozenset((node_id, other_node_id)))
                        self.nodes_dict[node_id].vpn_neighbours_set.add(other_node_id)
                    else:
                        self.nodes_dict[node_id].mesh_neighbours_set.add(other_node_id)

        if vpn_neighbours:
            result = self.nodes_dict[node_id].mesh_neighbours_set.union(self.nodes_dict[node_id].vpn_neighbours_set)
        else:
            result = self.nodes_dict[node_id].mesh_neighbours_set

        return result, fake_mesh_connections

    def get_mesh_of_node(self, node_id):
        return self.get_mesh_of_node_find_fake_meshes(node_id)[0]

    def get_mesh_of_node_find_fake_meshes(self, node_id):
        mesh_nodes_set = {node_id}
        fake_mesh_connections = set()
        last_len = 0
        # while mesh_nodes_set is growing...
        while last_len != len(mesh_nodes_set):
            last_len = len(mesh_nodes_set)
            for mesh_node in mesh_nodes_set:
                neighbours, fakes = self.get_neighbours_of_node_find_fake_meshes(mesh_node, vpn_neighbours=False)
                mesh_nodes_set = mesh_nodes_set.union(neighbours)
                fake_mesh_connections = fake_mesh_connections.union(fakes)
        return mesh_nodes_set, fake_mesh_connections

    def get_meshes(self):
        meshes_set = set()
        for node_id in self.nodes_dict:
            if self.get_node(node_id).is_online:
                mesh_nodes_set = self.get_mesh_of_node(node_id)
                meshes_set.add(frozenset(mesh_nodes_set))
        return meshes_set

    def get_nodes_in_tier(self, tier):
        if 0 not in self.tiers_dict:
            return set()  # If not even tier 0 is filled we can skip this shit and go home.

        for i in range(tier):
            if i+1 in self.tiers_dict:
                continue  # The next tier already exists? Fine.
            # Next tier does not exist, so we'll create it.
            tier_set = set()
            for node_id in self.tiers_dict[i]:  # Iterate over all nodes in the current tier.
                # Add all neighbours of this node to the set for the next tier.
                tier_set = tier_set.union(self.get_neighbours_of_node(node_id, vpn_neighbours=True))
            # Remove all node_ids that are already part of a tier.
            tier_set = tier_set.difference(self.tier_nodes_set)
            self.tiers_dict[i+1] = tier_set
            self.tier_nodes_set = self.tier_nodes_set.union(tier_set)

        return self.tiers_dict[tier]


class Node:
    def __init__(self, json_representation):
        self.json = json_representation
        self.mesh_neighbours_set = None
        self.vpn_neighbours_set = None

    @property
    def node_id(self):
        return self.json['nodeinfo']['node_id']

    @property
    def is_gateway(self):
        return self.json['flags']['gateway']

    @property
    def is_online(self):
        return self.json['flags']['online']

    @property
    def version(self):
        try:
            return Version(self.json['nodeinfo']['software']['firmware']['release'])
        except KeyError:
            pass

    @property
    def client_count(self):
        return self.json["statistics"]["clients"]

    @property
    def hostname(self):
        return self.json["nodeinfo"]["hostname"]

    @property
    def ipv6(self):
        """Return the ipv6 under which the device is reachable from the client network."""
        return self.json['nodeinfo']['network']['addresses'][0]

    @property
    def location(self) -> Union[tuple, None]:
        """Return a tupel of latitude and longitude, if present."""
        try:
            buffer = self.json['nodeinfo']['location']
            coordinate = (buffer['latitude'], buffer['longitude'])
            return coordinate
        except KeyError:
            pass


class Version:
    """
    Represent a gluon-firmware version.

    This one should make it easier to compare and represent different versions of the gluon firmware.
    Later, it may be possible to even match features of different versions.

    """

    def __init__(self, version_string):
        self.version_string = version_string

    @property
    def major(self):
        """Return the major-part of the version."""
        return self.version_string.split(".")[0]

    @property
    def minor(self):
        """Return the minor-part of the version."""
        return re.findall(r"\.(\d*)", self.version_string)[0]

    @property
    def build(self):
        """Return the build-character(s) of the version."""
        return re.findall(r"([a-zA-Z]*)-", self.version_string)[0]

    @property
    def builddate(self):
        """
        Return the builddate of the version.

        Returns a datetime.datetime.date object, so the precision is limited to days.

        """
        return datetime.datetime.strptime(self.version_string[-8:], "%Y%m%d").date()


class Link:
    def __init__(self, source, target, vpn, tq, bidirect):
        self.source = source
        self.target = target
        self.vpn = vpn
        self.tq = tq
        self.bidirect = bidirect

    @property
    def tq_percent(self):
        return 1/self.tq


def generate_from_file_objects(nodes_json_file, graph_json_file):
    net = Network()
    nodes_json = json.load(nodes_json_file)
    for node in nodes_json['nodes']:
        node_obj = Node(node)
        net.add_node(node_obj)

    graph_json = json.load(graph_json_file)
    node_id_list = []
    for node in graph_json['batadv']['nodes']:
        node_id_list.append(node['node_id'])
    for link in graph_json['batadv']['links']:
        net.add_link(Link(node_id_list[link['source']],
                          node_id_list[link['target']],
                          link['vpn'],
                          link['tq'],
                          link['bidirect']))
    return net


def generate_from_files(nodes_json_path, graph_json_path):
    with open(nodes_json_path, "r") as nodes_json:
        with open(graph_json_path, "r") as graph_json:
            return generate_from_file_objects(nodes_json, graph_json)


def generate_from_urls(nodes_json_url, graph_json_url):
    with urllib.request.urlopen(nodes_json_url) as nodes_json:
        with urllib.request.urlopen(graph_json_url) as graph_json:
            return generate_from_file_objects(nodes_json, graph_json)


def main(nodes_json_path, graph_json_path):
    net = generate_from_files(nodes_json_path, graph_json_path)
    print(net.get_neighbours_of_node("a0f3c112e932", vpn_neighbours=False))
    print(net.get_neighbours_of_node("a0f3c112e932", vpn_neighbours=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('nodesJSON')
    parser.add_argument('graphJSON')
    args = parser.parse_args()

    main(args.nodesJSON, args.graphJSON)
