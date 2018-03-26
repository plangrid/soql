import unittest

from soql import attributes
from soql import Model
from soql.path_builder import PathBuilder
from tests.helpers import SoqlAssertions


# Declare the relationships separately so we can assert some stuff in the tests
# more easily...
next_ = attributes.Relationship('Next', related_model='LinkedList')
list_ = attributes.Relationship('List', related_model='LinkedList')
children = attributes.Relationship('Children', related_model='GraphNode', many=True)


class LinkedList(Model):
    id = attributes.Integer('Id')
    next = next_


class GraphNode(Model):
    id = attributes.Integer('Id')
    value = attributes.Integer('Value')
    list = list_
    children = children


class PathBuilderTest(unittest.TestCase, SoqlAssertions):
    def assertColumnNodesEqual(self, node_list, expected):
        self.assertEqual(
            sorted([str(node) for node in node_list]),
            sorted(expected)
        )

    def test_getattr(self):
        self.assertSoqlEqual(LinkedList.id, 'LinkedList.Id')
        self.assertSoqlEqual(LinkedList.next.id, 'LinkedList.Next.Id')
        self.assertSoqlEqual(LinkedList.next.next.id, 'LinkedList.Next.Next.Id')
        self.assertSoqlEqual(GraphNode.children.list.next.id, 'GraphNode.Children.List.Next.Id')
        self.assertSoqlEqual(GraphNode.children.children, 'GraphNode.Children.Children')

    def test_get_relationship_attr_in_path(self):
        path = GraphNode.children.list.next
        self.assertEqual(path.get_relationship_attr_in_path(path_index=0), children)
        self.assertEqual(path.get_relationship_attr_in_path(path_index=1), list_)
        self.assertEqual(path.get_relationship_attr_in_path(path_index=2), next_)
        self.assertEqual(path.get_relationship_attr_in_path(path_index=-1), next_)

    def test_get_model_in_path(self):
        path = GraphNode.children.list.next
        self.assertEqual(path.get_model_in_path(path_index=0), GraphNode)
        self.assertEqual(path.get_model_in_path(path_index=1), LinkedList)
        self.assertEqual(path.get_model_in_path(path_index=2), LinkedList)
        self.assertEqual(path.get_model_in_path(path_index=-1), LinkedList)

    def test_get_last_model_column_nodes(self):
        path_builder = PathBuilder(model=GraphNode)
        self.assertColumnNodesEqual(
            path_builder.get_last_model_column_nodes(),
            ['GraphNode.Id', 'GraphNode.Value']
        )

        path_builder = path_builder.extend_path('children')
        self.assertColumnNodesEqual(
            path_builder.get_last_model_column_nodes(),
            ['GraphNode.Children.Id', 'GraphNode.Children.Value']
        )

        path_builder = path_builder.extend_path('list')
        self.assertColumnNodesEqual(
            path_builder.get_last_model_column_nodes(),
            ['GraphNode.Children.List.Id']
        )

