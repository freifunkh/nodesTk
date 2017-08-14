#!/usr/bin/python3

import argparse
import json
import re
import datetime


class Network:
    def __init__(self):
        self.nodes_dict = dict()  # node_id as key and Node obj as value
        self.links_dict = dict()  # node_ids alphabetically concatenated as key and Link obj as value
        self.tiers_dict = dict()  # tier number as key and set of node_id as value
        self.tier_nodes_set = set()  # a set of all node_id who already have a tier

    def add_link(self, newlink):
        l = [newlink.source, newlink.target]
        l.sort(key=str.lower)
        self.links_dict["-".join(l)] = newlink  # now with 'Streckenstrich'(tm)

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
                    else:
                        self.nodes_dict[node_id].mesh_neighbours_set.add(other_node_id)

        if vpn_neighbours:
            return self.nodes_dict[node_id].mesh_neighbours_set.union(self.nodes_dict[node_id].vpn_neighbours_set)
        else:
            return self.nodes_dict[node_id].mesh_neighbours_set

    def get_mesh_of_node(self, node_id):
        mesh_nodes_set = {node_id}
        last_len = 0
        # while mesh_nodes_set is growing...
        while last_len != len(mesh_nodes_set):
            last_len = len(mesh_nodes_set)
            for mesh_node in mesh_nodes_set:
                mesh_nodes_set = mesh_nodes_set.union(self.get_neighbours_of_node(mesh_node, vpn_neighbours=False))
        return mesh_nodes_set

    def get_meshes(self):
        meshes_set = set()
        for node_id in self.nodes_dict:
            mesh_nodes_set = self.get_mesh_of_node(node_id)
            mesh_str = '-'.join(sorted(list(mesh_nodes_set)))
            #meshes_set.add(frozenset(mesh_nodes_set))
            meshes_set.add(mesh_str)
        return meshes_set

    def get_online_meshes(self):
        meshes_set = set()
        for node_id in self.nodes_dict:
            if self.get_node(node_id).is_online:
                mesh_nodes_set = self.get_mesh_of_node(node_id)
                mesh_str = '-'.join(sorted(list(mesh_nodes_set)))
                meshes_set.add(mesh_str)
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


class Version:
    def __init__(self, version_string):
        self.version_string = version_string

    @property
    def major(self):
        return self.version_string.split(".")[0]

    @property
    def minor(self):
        return re.findall(r"\.(\d*)", self.version_string)[0]

    @property
    def build(self):
        return re.findall(r"([a-zA-Z]*)-", self.version_string)[0]

    @property
    def builddate(self):
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


def generate_from_files(nodes_json_path, graph_json_path):
    net = Network()
    with open(nodes_json_path, 'r') as f:
        nodes_json = json.load(f)
        for node in nodes_json['nodes']:
            node_obj = Node(node)
            net.add_node(node_obj)

    with open(graph_json_path, 'r') as f:
        graph_json = json.load(f)
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


def main(nodes_json_path, graph_json_path):
    net = generate_from_files(nodes_json_path, graph_json_path)

#    print(net.get_neighbours_of_node("a0f3c112e932", vpn_neighbours=False))
#    print(net.get_neighbours_of_node("a0f3c112e932", vpn_neighbours=True))

    for mesh in sorted(net.get_meshes()):
        print(mesh)
    print(len(net.get_meshes()))
    print(len(net.get_nodes_in_tier(1)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('nodesJSON')
    parser.add_argument('graphJSON')
    args = parser.parse_args()

    main(args.nodesJSON, args.graphJSON)
