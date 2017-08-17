#!/usr/bin/python3

import unittest
import sys
from io import StringIO
import nodesTk
import datetime


def validate_get_mesh_of_node(self, node_id):
    done = []
    todo = [node_id]
    for upcoming_id in todo:
        if upcoming_id not in done:
            done.append(upcoming_id)
            neighbours = self.get_neighbours_of_node(upcoming_id)
            for each_neighbour in neighbours:
                if each_neighbour not in done:
                    todo.append(each_neighbour)
    return done


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

    def test_node_ip(self):
        """Test the ipv6 adress of a node, that should be reachable from the client net"""
        assert 'fdca:ffee:8:0:a2f3:c1ff:fe12:e932' == self.net.get_node("a0f3c112e932").ipv6

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

    def test_version_of_node(self):
        assert isinstance(self.net.get_node("60e327e719bc").version, nodesTk.Version)

    def test_not_existing_version_of_node(self):
        assert self.net.get_node("62d703f9b069").version is None

    @unittest.skip("this one lasts way too long")
    def test_number_of_meshes(self):
        # Fixme: actually the test passes, but with 477 being lesser than 480.
        # The result is such a close run, that there must still be an error in our equation.
        assert len(self.net.get_meshes()) <= len(self.net.get_nodes_in_tier(1))

    def test_meshnodes(self):
        res = nodesTk.Network.get_mesh_of_node(self.net, "14cc20704b0e")
        assert 6 == len(res)
        assert {'14cc20704b0e', 'e894f6519000', 'e894f641b492',
                'f4f26d4a24fe', '10feedf14cde', 'ec086bc987c4'}.issubset(res)

    def test_validate_meshnodes(self):
        assert nodesTk.Network.get_mesh_of_node(self.net, "14cc20704b0e")\
               == set(validate_get_mesh_of_node(self.net, "14cc20704b0e"))

    @unittest.skip("this one lasts way too long")
    def test_number_of_online_meshes(self):
        assert 477 == len(self.net.get_meshes())


class NodesTKGatewaylessTestCase(unittest.TestCase):
    def setUp(self):
        self.net = nodesTk.generate_from_files("gatewayless_nodes.json", "graph.json")

    def test_nodeamount(self):
        assert 1139 == len(self.net.nodes_dict)

    def test_gatewayamount(self):
        assert 0 == len(self.net.get_nodes_in_tier(0))

    def test_uplinkamount(self):
        assert 0 == len(self.net.get_nodes_in_tier(1))


class NodesTKVersionTests(unittest.TestCase):
    @staticmethod
    def test_version():
        assert hasattr(nodesTk, 'Version')

    @staticmethod
    def test_version_init():
        assert hasattr(nodesTk.Version, '__init__') and nodesTk.Version("0.14f-20170411")

    @staticmethod
    def test_version_string():
        version_str = "0.14f-20170411"
        assert version_str == nodesTk.Version(version_str).version_string

    @staticmethod
    def test_major():
        assert "0" == nodesTk.Version("0.14f-20170411").major

    @staticmethod
    def test_minor():
        assert "14" == nodesTk.Version("0.14f-20170411").minor

    @staticmethod
    def test_build():
        assert "f" == nodesTk.Version("0.14f-20170411").build

    @staticmethod
    def test_builddate():
        bd = nodesTk.Version("0.14f-20170411").builddate
        assert "2017-04-11" == str(bd)
        assert datetime.date == type(bd)

if __name__ == '__main__':
    unittest.main()
