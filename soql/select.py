"""
    Select
    ~~~~~~

    Entrypoint for generating SOQL from models.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

from __future__ import absolute_import
from collections import OrderedDict
from copy import copy

from soql.nodes import SubqueryClause
from soql.nodes import OrderByClause
from soql.nodes import Count
from soql.nodes import SelectClause
from soql.path_builder import PathBuilder
from soql.utils import to_unicode


class SelectClauseIsntValidSubquery(Exception):
    pass


class RelationshipNode(object):
    """
    Joins can be recursive. This little class let's us represent all the joined
    relationships of a select query as a graph.
    """
    def __init__(self, relationship=None):
        """
        Constructs a new node in a graph.

        :param str|NoneType relationship: The attribute name of the
            relationship. None represents the root node.
        """
        self.relationship = relationship

        # It helps testability tremendously if the joins come in a
        # reliable order... hence the OrderedDict
        self.child_relationships = OrderedDict()

    def __copy__(self):
        node = RelationshipNode(relationship=self.relationship)
        node.child_relationships = copy(self.child_relationships)
        return node

    def __iter__(self):
        for value in self.child_relationships.values():
            yield value

    def add_child(self, relationship):
        """Adds a child node."""
        self.child_relationships[relationship] = RelationshipNode(relationship)

    def add_path(self, path):
        """Adds the complete path to this node, creating any child nodes that
        don't exist yet."""
        node = self
        for relationship in path:
            if relationship not in node.child_relationships:
                node.add_child(relationship)
            node = node.child_relationships[relationship]


class SelectClauseBuilder(object):
    """
    Builds SOQL SELECT statements.
    """
    def __init__(self, model):
        """
        The model being selected from.

        :param admin_api_2.salesforce.orm.model.Model model:
        """
        self._model = model
        self._columns = PathBuilder(model=self._model).get_last_model_column_nodes()
        self._relationship_graph = RelationshipNode()
        self._order_bys = []
        self._filters = []
        self._limit = None
        self._offset = None
        self._count = False

    def __copy__(self):
        builder = SelectClauseBuilder(model=self._model)
        builder._columns = copy(self._columns)
        builder._filters = copy(self._filters)
        builder._order_bys = copy(self._order_bys)
        builder._relationship_graph = copy(self._relationship_graph)
        builder._limit = self._limit
        builder._offset = self._offset
        builder._count = self._count
        return builder

    def join(self, path_builder):
        """
        Add a join to the clause.

        :param path_builder:
        :rtype: SelectClauseBuilder
        """
        self._relationship_graph.add_path(path_builder.path)
        return copy(self)

    def where(self, expression):
        """
        Add a filter to the clause.

        :param expression:
        :rtype: SelectClauseBuilder
        """
        self._filters.append(expression)
        return copy(self)

    def order_by(self, column, direction=None, nulls_position=None):
        """
        Order the results of the clause.

        :param column:
        :param str direction: optionally declare the direction to order.
        :param str nulls_position: optionally declare whether the null values
            should be at the top or bottom of the results.
        :rtype: SelectClauseBuilder
        """
        clause = OrderByClause(
            column=column,
            direction=direction,
            nulls_position=nulls_position
        )
        self._order_bys.append(clause)

        return copy(self)

    def limit(self, limit):
        """
        Limit the amount of results.

        :param limit:
        :rtype: SelectClauseBuilder
        """
        self._limit = limit
        return copy(self)

    def offset(self, offset):
        """
        Skip the first amount of results.

        :param offset:
        :rtype: SelectClauseBuilder
        """
        self._offset = offset
        return copy(self)

    def count(self):
        """
        Instead of fetching the results, just count the total.

        :rtype: SelectClauseBuilder
        """
        self._count = True
        return copy(self)

    def columns(self, *columns):
        """
        Override the columns that are selected.

        :param columns:
        :rtype: SelectClauseBuilder
        """
        self._columns = list(columns)
        return copy(self)

    def subquery(self):
        """
        Convert the clause to a subquery. This is useful for things like...

            subquery = select(SomeModel.id).where(SomeModel.id == 123).subquery()

            select(SomeOtherModel).where(SomeOtherModel.fk.in_(subquery))

        :rtype: admin_api_2.salesforce.orm.soql.SubqueryClause
        """
        if self._order_bys or self._limit or self._offset:
            raise SelectClauseIsntValidSubquery()

        return SubqueryClause(
            select_columns=self._get_columns(),
            from_table=self._model.__soql_name__(),
            where_conditions=self._filters
        )

    def __unicode__(self):
        """Converts the instance to a SOQL string."""
        return to_unicode(self._get_select_clause())

    def __str__(self):
        return str(self._get_select_clause())

    def _get_columns(self):
        if self._count:
            return [Count()]

        joins = self._compile_joins()
        return self._columns + joins

    def _get_select_clause(self):
        return SelectClause(
            select_columns=self._get_columns(),
            from_table=self._model.__soql_name__(),
            where_conditions=self._filters,
            order_bys=self._order_bys,
            limit=self._limit,
            offset=self._offset
        )

    def _compile_joins(self):
        return self._recursively_compile_joins(
            path=PathBuilder(model=self._model),
            node=self._relationship_graph
        )

    def _recursively_compile_joins(self, path, node):
        """
        Depth-first-searches the relationship graph to build a SOQL
        representation of the joins.

        :param admin_api_2.salesforce.orm.path_builder.PathBuilder path:
        :param RelationshipNode node:
        :return: list of join clauses
        """
        joins = []

        for child_node in node:
            child_path = path.extend_path(child_node.relationship)
            attr = child_path.get_relationship_attr_in_path(path_index=-1)
            if attr.many:
                # Joining a one-to-many relationship needs to be done as a
                # subquery, where the subquery is scoped to the object being
                # joined.
                aggregate_join = self._recursively_compile_joins(
                    path=PathBuilder(model=attr.related_model),
                    node=child_node
                )
                from_table = child_path.get_column_node()
                subquery = SubqueryClause(
                    select_columns=aggregate_join,
                    from_table=from_table,
                )
                joins.append(subquery)

            else:
                column_joins = self._recursively_compile_joins(
                    path=child_path,
                    node=child_node
                )

                # The joined columns need to come before any subqueries
                joins = column_joins + joins

        if node.relationship is None:
            # Looks like we're back at the root node.
            return joins

        joins = path.get_last_model_column_nodes() + joins
        return joins


select = SelectClauseBuilder
