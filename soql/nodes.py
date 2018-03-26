"""
    Nodes
    ~~~~~

    Nodes for using composite pattern to implement a query builder.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from datetime import datetime

import six
from dateutil.tz import tzutc

from soql.utils import AttrDict
from soql.utils import to_unicode


# The various operations you can perform in SOQL
OPS = AttrDict(
    AND='AND',
    OR='OR',
    NOT='NOT',
    EQ='=',
    LT='<',
    LTE='<=',
    GT='>',
    GTE='>=',
    NE='!=',
    IN='IN',
    NOT_IN='NOT IN',
    IS='IS',
    IS_NOT='IS NOT',
    LIKE='LIKE',
    INCLUDES='INCLUDES',
    EXCLUDES='EXCLUDES'
)

# Reserved SOQL words
WORDS = AttrDict(
    SELECT='SELECT',
    FROM='FROM',
    WHERE='WHERE',
    GROUP_BY='GROUP BY',
    ORDER_BY='ORDER BY',
    LIMIT='LIMIT',
    OFFSET='OFFSET',
    ASC='ASC',
    DESC='DESC',
    NULL='NULL',
    TRUE='TRUE',
    FALSE='FALSE',
    NULLS_FIRST='NULLS FIRST',
    NULLS_LAST='NULLS LAST'
)

# SOQL functions
FUNCTIONS = AttrDict(
    AVG='AVG',
    COUNT='COUNT',
    COUNT_DISTINCT='COUNT_DISTINCT',
    MIN='MIN',
    MAX='MAX',
    SUM='SUM'
)


def _stringify(value):
    """Converts a native Python object to its SOQL representation."""
    if isinstance(value, six.string_types):
        return "'{}'".format(value)
    if value is None:
        return WORDS.NULL
    if value is True:
        return WORDS.TRUE
    if value is False:
        return WORDS.FALSE
    if isinstance(value, datetime):
        if not value.tzinfo:
            return value.replace(tzinfo=tzutc()).isoformat()
        else:
            return value.isoformat()
    return str(value)


class Node(object):
    """Base node for building a graph representation of a SOQL query."""
    def __init__(self, child_nodes, sep=''):
        self.child_nodes = child_nodes
        self.sep = sep

    def _as_string(self, method):
        return self.sep.join([method(node) for node in self.child_nodes])

    def __unicode__(self):
        return to_unicode(self._as_string(to_unicode))

    def __str__(self):
        return str(self._as_string(str))


class Grouped(Node):
    def __init__(self, node, braces='()'):
        super(Grouped, self).__init__(child_nodes=[braces[0], node, braces[1]])


class Expression(Node):
    def __init__(self, lhs, op, rhs):
        child_nodes = [_stringify(lhs), op, _stringify(rhs)]
        super(Expression, self).__init__(child_nodes=child_nodes, sep=' ')


class CommaSeparated(Node):
    def __init__(self, items):
        super(CommaSeparated, self).__init__(child_nodes=items, sep=', ')


class AndSeparated(Node):
    def __init__(self, items):
        sep = ' {} '.format(OPS.AND)
        super(AndSeparated, self).__init__(child_nodes=items, sep=sep)


class Array(Node):
    def __init__(self, items):
        array = Grouped(node=CommaSeparated(items=items))
        super(Array, self).__init__(child_nodes=[array])


class Function(Node):
    def __init__(self, function_name, args=None):
        child_nodes = [function_name, Array(args or [])]
        super(Function, self).__init__(child_nodes=child_nodes, sep='')


class Count(Function):
    def __init__(self, field_name=None):
        args = [field_name] if field_name is not None else []
        super(Count, self).__init__(function_name=FUNCTIONS.COUNT, args=args)


class SelectClause(Node):
    def __init__(
            self,
            select_columns,
            from_table,
            where_conditions=None,
            order_bys=None,
            limit=None,
            offset=None
    ):
        nodes = [
            WORDS.SELECT,
            CommaSeparated(items=select_columns),
            WORDS.FROM,
            from_table
        ]

        if where_conditions:
            nodes.append(WORDS.WHERE)
            nodes.append(AndSeparated(items=where_conditions))

        if order_bys:
            nodes.append(WORDS.ORDER_BY)
            nodes.append(CommaSeparated(items=order_bys))

        if limit is not None:
            nodes.append(WORDS.LIMIT)
            nodes.append(Node(child_nodes=[limit]))

        if offset is not None:
            nodes.append(WORDS.OFFSET)
            nodes.append(Node(child_nodes=[offset]))

        super(SelectClause, self).__init__(child_nodes=nodes, sep=' ')


class OrderByClause(Node):
    def __init__(self, column, direction=None, nulls_position=None):
        child_nodes = [column]
        if direction:
            child_nodes.append(direction)
        if nulls_position:
            child_nodes.append(nulls_position)
        super(OrderByClause, self).__init__(child_nodes=child_nodes, sep=' ')


class SubqueryClause(Node):
    def __init__(
            self,
            select_columns,
            from_table,
            where_conditions=None
    ):
        query = SelectClause(
            select_columns=select_columns,
            from_table=from_table,
            where_conditions=where_conditions
        )
        grouped = Grouped(node=query)
        super(SubqueryClause, self).__init__(child_nodes=[grouped])


def _op_factory(op):
    """Quick little factory for a little bit of DRY when defining magic methods
    on Operatable."""
    def inner(self, rhs):
        return Expression(lhs=self, op=op, rhs=rhs)
    return inner


def _get_container_node(value):
    """Used for building container expressions - the input could either be
    a Python iterable, or another node."""
    if isinstance(value, Node):
        # This looks like a subquery!
        return value
    else:
        return Array(items=[_stringify(i) for i in value])


class Operatable(object):
    """A mixin to give a node operation functionality. I.e., this is where
    some of the magic happens, and allows for the nice filter syntax:

        SomeModel.name == 'John'
        SomeModel.id.in_([1, 2, 3])
        etc.
    """
    __eq__ = _op_factory(OPS.EQ)
    __ne__ = _op_factory(OPS.NE)
    __gt__ = _op_factory(OPS.GT)
    __ge__ = _op_factory(OPS.GTE)
    __lt__ = _op_factory(OPS.LT)
    __le__ = _op_factory(OPS.LTE)

    def like_(self, value):
        return Expression(lhs=self, op=OPS.LIKE, rhs=value)

    def in_(self, iterable):
        container = _get_container_node(value=iterable)
        return Expression(lhs=self, op=OPS.IN, rhs=container)

    def not_in_(self, iterable):
        container = _get_container_node(value=iterable)
        return Expression(lhs=self, op=OPS.NOT_IN, rhs=container)


class ColumnPath(Node, Operatable):
    def __init__(self, *elements):
        super(ColumnPath, self).__init__(child_nodes=elements, sep='.')


def _logical_expression(nodes, op):
    expression = Expression(lhs=nodes[0], op=op, rhs=nodes[1])
    for node in nodes[2:]:
        expression = Expression(lhs=expression, op=op, rhs=node)
    return Grouped(node=expression)


def and_(*nodes):
    return _logical_expression(nodes=nodes, op=OPS.AND)


def or_(*nodes):
    return _logical_expression(nodes=nodes, op=OPS.OR)


def not_(node):
    return Node(child_nodes=[OPS.NOT, node], sep=' ')


# These values are needed publicly, so we'll create some nice aliases.
asc = WORDS.ASC
desc = WORDS.DESC
nulls_first = WORDS.NULLS_FIRST
nulls_last = WORDS.NULLS_LAST


