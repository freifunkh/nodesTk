#!/usr/bin/python3

import argparse
import json


class Network():
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
        node_id = node.get_node_id()
        self.nodes_dict[node_id] = node
        if node.is_gateway():
            self.add_node_to_tier(node_id, 0)

    def get_node(self, node_id):
        return self.nodes_dict[node_id]

    def add_node_to_tier(self, node_id, tier):
        if node_id in self.tier_nodes_set:
            return
        if not tier in self.tiers_dict:
            self.tiers_dict[tier] = set()
        self.tiers_dict[tier].add(node_id)
        self.tier_nodes_set.add(node_id)

    def get_neighbours_of_node(self, node_id):
        if self.nodes_dict[node_id].neighbours_set:
            return self.nodes_dict[node_id].neighbours_set
        neighbours_set = set()
        for link_id in self.links_dict:
            if self.links_dict[link_id].source == node_id:
                neighbours_set.add(self.links_dict[link_id].target)
            elif self.links_dict[link_id].target == node_id:
                neighbours_set.add(self.links_dict[link_id].source)
        self.nodes_dict[node_id].neighbours_set = neighbours_set
        return neighbours_set

    def get_nodes_in_tier(self, tier):
        if not 0 in self.tiers_dict:
            return set()  # If not even tier 0 is filled we can skip this shit and go home.

        for i in range(tier):
            if i+1 in self.tiers_dict:
                continue  # The next tier already exists? Fine.
            # Next tier does not exist, so we'll create it.
            tier_set = set()
            for node_id in self.tiers_dict[i]:  # Iterate over all nodes in the current tier.
                tier_set = tier_set.union(self.get_neighbours_of_node(node_id)) # Add all neighbours of this node to the set for the next tier.
            tier_set = tier_set.difference(self.tier_nodes_set)  # Remove all node_ids that are already part of a tier.
            self.tiers_dict[i+1] = tier_set
            self.tier_nodes_set = self.tier_nodes_set.union(tier_set)

        return self.tiers_dict[tier]


class Node():
    def __init__(self, json):
        self.json = json
        self.neighbours_set = None

    def get_node_id(self):
        return self.json['nodeinfo']['node_id']

    def is_gateway(self):
        return self.json['flags']['gateway']

    def is_online(self):
            return self.json['flags']['online']


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

    print(net.get_neighbours_of_node('30b5c281433e'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('nodesJSON')
    parser.add_argument('graphJSON')
    args = parser.parse_args()

    main(args.nodesJSON, args.graphJSON)
