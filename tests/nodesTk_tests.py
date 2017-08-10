#!/usr/bin/python3

import unittest
import sys
from io import StringIO
import nodesTk


class NodesTKTestCase(unittest.TestCase):
    def setUp(self):
        self.net = nodesTk.generate_from_files("nodes.json", "graph.json")

    def test_nodeamount(self):
        assert 1139 == len(self.net.nodes_dict)

    def test_gatewayamount(self):
        assert 8 == len(self.net.get_nodes_in_tier(0))

    def test_uplinkamount(self):
        assert 480 == len(self.net.get_nodes_in_tier(1))

    @staticmethod
    def test_addlink_naming():
        l = nodesTk.Link("62d703f9b069", "18a6f72b7c36", True, 1, False)
        new_net = nodesTk.Network()
        new_net.add_link(l)
        assert list(new_net.links_dict.keys())[0] == "18a6f72b7c36-62d703f9b069"

    @staticmethod
    def test_tq_property():
        l = nodesTk.Link("a", "b", True, 1.337, False)
        assert abs(l.tq_percent-0.7479431563201197) < 0.0001

    def test_get_neighbours(self):
        assert self.net.get_neighbours_of_node("a0f3c112e932", vpn_neighbours=False) == {"6466b3b0256e"}
        assert self.net.get_neighbours_of_node("a0f3c112e932", vpn_neighbours=True) == {"6466b3b0256e", "9e9203c5c897"}

    def test_node_online(self):
        assert self.net.get_node("62d703f9b069").is_online()

    @staticmethod
    def test_main():
        captured_output = StringIO()
        sys.stdout = captured_output  # redirect stdout
        nodesTk.main("nodes.json", "graph.json")
        sys.stdout = sys.__stdout__  # reset redirect
        assert captured_output.getvalue().startswith("{'6466b3b0256e'}\n{'6466b3b0256e', '9e9203c5c897'}\n")


if __name__ == '__main__':
    unittest.main()
