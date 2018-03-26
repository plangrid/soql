#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from datetime import date, datetime

from dateutil.tz import tzutc

from soql.nodes import ColumnPath, Expression, OPS, _stringify
from soql.nodes import and_, or_, not_
from tests.helpers import SoqlAssertions


class ExpressionTest(unittest.TestCase, SoqlAssertions):
    def test_operations(self):
        for operation in OPS.values():
            exp = Expression(lhs=123, op=operation, rhs=456)
            self.assertSoqlEqual(exp, '123 {} 456'.format(operation))

    def test_chained_expressions(self):
        exp1 = Expression(lhs=123, op=OPS.EQ, rhs=456)
        exp2 = Expression(lhs=789, op=OPS.AND, rhs=exp1)
        self.assertSoqlEqual(exp2, '789 AND 123 = 456')

    def test_type_rendering(self):
        exp1 = Expression(lhs='123', op=OPS.EQ, rhs=456)
        self.assertSoqlEqual(exp1, "'123' = 456")

        exp2 = Expression(lhs='789', op=OPS.AND, rhs=exp1)
        self.assertSoqlEqual(exp2, "'789' AND '123' = 456")


class StringifyTest(unittest.TestCase):
    def test_stringify(self):
        self.assertEqual(_stringify('Apples'), "'Apples'")

        self.assertEqual(_stringify(u'CATMONKÈ-123490'), u"'CATMONKÈ-123490'")

        self.assertEqual(_stringify(1), '1')

        self.assertEqual(_stringify(True), 'TRUE')

        self.assertEqual(_stringify(False), 'FALSE')

        self.assertEqual(_stringify(None), 'NULL')

        date_ = date(year=1990, month=10, day=19)
        self.assertEqual(_stringify(date_), '1990-10-19')

        datetime_ = datetime(
            year=1990,
            month=10,
            day=19,
            hour=1,
            minute=2,
            second=3,
            tzinfo=tzutc()
        )

        self.assertEqual(_stringify(datetime_), '1990-10-19T01:02:03+00:00')

        naive_datetime = datetime(
            year=1990,
            month=10,
            day=19,
            hour=1,
            minute=2,
            second=3
        )
        self.assertEqual(_stringify(naive_datetime), '1990-10-19T01:02:03+00:00')


class OperationsTest(unittest.TestCase):
    def test_operations(self):
        column_path = ColumnPath('Monkey.Tail')

        self.assertEqual(str(column_path == '123'), "Monkey.Tail = '123'")
        self.assertEqual(str(column_path == 56), "Monkey.Tail = 56")

        self.assertEqual(str(column_path < 5), "Monkey.Tail < 5")
        self.assertEqual(str(column_path > 5), "Monkey.Tail > 5")
        self.assertEqual(str(column_path <= 5), "Monkey.Tail <= 5")
        self.assertEqual(str(column_path >= 5), "Monkey.Tail >= 5")

        self.assertEqual(str(column_path != None), "Monkey.Tail != NULL")
        self.assertEqual(str(column_path == True), "Monkey.Tail = TRUE")
        self.assertEqual(str(column_path == False), "Monkey.Tail = FALSE")

        self.assertEqual(
            str(column_path.like_('Va%')),
            "Monkey.Tail LIKE 'Va%'"
        )
        self.assertEqual(
            str(column_path.in_(['Jin', 'Jan'])),
            "Monkey.Tail IN ('Jin', 'Jan')"
        )
        self.assertEqual(
            str(column_path.in_([u'Jin', u'Jan'])),
            "Monkey.Tail IN ('Jin', 'Jan')"
        )
        self.assertEqual(
            str(column_path.not_in_(['Jin', 'Jan'])),
            "Monkey.Tail NOT IN ('Jin', 'Jan')"
        )

        self.assertEqual(
            str(and_(column_path == 'R', column_path < 10)),
            "(Monkey.Tail = 'R' AND Monkey.Tail < 10)"
        )
        self.assertEqual(
            str(and_(column_path == 'R', column_path < 10, column_path != 'G')),
            "(Monkey.Tail = 'R' AND Monkey.Tail < 10 AND Monkey.Tail != 'G')"
        )

        self.assertEqual(
            str(or_(column_path == 'R', column_path < 10)),
            "(Monkey.Tail = 'R' OR Monkey.Tail < 10)"
        )
        self.assertEqual(
            str(or_(column_path == 'R', column_path < 10, column_path != 'G')),
            "(Monkey.Tail = 'R' OR Monkey.Tail < 10 OR Monkey.Tail != 'G')"
        )

        self.assertEqual(
            str(not_(column_path == 'R')),
            "NOT Monkey.Tail = 'R'"
        )

        self.assertEqual(
            str(not_(and_(column_path == 'R',
                          or_(column_path == 10, column_path == 'G')))),
            "NOT (Monkey.Tail = 'R' AND (Monkey.Tail = 10 OR Monkey.Tail = 'G'))"
        )
