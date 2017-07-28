#!/usr/bin/python3

import json


class Network():
    def __init__(self):
        self.nodes_dict = dict()

    def add_node(self, node):
        node_id = node['nodeinfo']['node_id']
        self.nodes_dict[node_id] = node


class Node():
    def __init__(self, json):
        self.json = json


class Link():
    def __init__(self):
        pass


if __name__ == "__main__":
    with open("nodes.json", 'r') as f:
        nodes_json = json.load(f)
        for node in nodes_json['nodes']:
            node_obj = Node(node)
            
