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

    def test_tier2amount(self):
        # unvalidated value
        assert 235 == len(self.net.get_nodes_in_tier(2))

    def test_tier3amount(self):
        # unvalidated value
        assert 104 == len(self.net.get_nodes_in_tier(3))

    def test_tier4amount(self):
        # unvalidated value
        assert 33 == len(self.net.get_nodes_in_tier(4))

    def test_tier5amount(self):
        # unvalidated value
        assert 13 == len(self.net.get_nodes_in_tier(5))

    def test_tier6amount(self):
        # unvalidated value
        assert 9 == len(self.net.get_nodes_in_tier(6))

    def test_tier7amount(self):
        # unvalidated value
        assert 1 == len(self.net.get_nodes_in_tier(7))

    def test_tier8amount(self):
        # unvalidated value
        assert 0 == len(self.net.get_nodes_in_tier(8))

    def test_tier456amount_again(self):
        # unvalidated value
        assert 33 == len(self.net.get_nodes_in_tier(4))
        assert 13 == len(self.net.get_nodes_in_tier(5))
        assert 9 == len(self.net.get_nodes_in_tier(6))

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
        assert self.net.get_node("62d703f9b069").is_online

    @staticmethod
    def test_main():
        captured_output = StringIO()
        sys.stdout = captured_output  # redirect stdout
        nodesTk.main("nodes.json", "graph.json")
        sys.stdout = sys.__stdout__  # reset redirect
        assert (captured_output.getvalue().startswith("{'6466b3b0256e'}\n{'6466b3b0256e', '9e9203c5c897'}\n") or
                captured_output.getvalue().startswith("{'6466b3b0256e'}\n{'9e9203c5c897', '6466b3b0256e'}\n"))

    def test_add_node_to_tier_twice(self):
        # this id got added once by the setup method at top
        assert 1 == len(self.net.get_nodes_in_tier(7))
        # and we'll try it a second time
        self.net.add_node_to_tier('940c6db3c798', 7)
        assert 1 == len(self.net.get_nodes_in_tier(7))

    @staticmethod
    def test_version():
        assert hasattr(nodesTk, 'Version')


class NodesTKGatewaylessTestCase(unittest.TestCase):
    def setUp(self):
        self.net = nodesTk.generate_from_files("gatewayless_nodes.json", "graph.json")

    def test_nodeamount(self):
        assert 1139 == len(self.net.nodes_dict)

    def test_gatewayamount(self):
        assert 0 == len(self.net.get_nodes_in_tier(0))

    def test_uplinkamount(self):
        assert 0 == len(self.net.get_nodes_in_tier(1))

if __name__ == '__main__':
    unittest.main()
