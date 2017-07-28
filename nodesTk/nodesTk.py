#!/usr/bin/python3

import json


class Network():
    def __init__(self):
        self.nodes_dict = dict() # node_id as key and Node obj as value
        self.tiers_dict = dict() # tier number as key and set of node_id as value
        self.tier_nodes_set = set() # a set of all node_id who already have a tier

    def add_node(self, node):
        node_id = node.get_node_id()
        self.nodes_dict[node_id] = node
        if node.is_gateway():
            self.add_node_to_tier(node_id, 0)

    def get_node(self, node_id):
        return self.nodes_dict(node_id)

    def add_node_to_tier(self, node_id, tier):
        if node_id in self.tier_nodes_set:
            return
        if not tier in self.tiers_dict:
            self.tiers_dict[tier] = set()
        self.tiers_dict[tier].add(node_id)
        self.tier_nodes_set.add(node_id)

    def get_nodes_in_tier(self, tier):
        if tier in self.tiers_dict:
            return self.tiers_dict[tier]
        return set()


class Node():
    def __init__(self, json):
        self.json = json

    def get_node_id(self):
        return self.json['nodeinfo']['node_id']

    def is_gateway(self):
        return self.json['flags']['gateway']


class Link():
    def __init__(self):
        pass


if __name__ == "__main__":
    net = Network()
    with open("nodes.json", 'r') as f:
        nodes_json = json.load(f)
        for node in nodes_json['nodes']:
            node_obj = Node(node)
            net.add_node(node_obj)

    print(net.get_nodes_in_tier(0))
