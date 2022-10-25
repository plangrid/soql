#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest
from datetime import datetime, date

from dateutil.tz import tzutc

from soql import attributes
from soql import NullSalesforceColumnError
from soql import Model


class RelatedModel(Model):
    id = attributes.Integer('Id')


class RelationshipTest(unittest.TestCase):
    def test_load(self):
        attr = attributes.Relationship('Attr', related_model=RelatedModel)
        data = {
            'attributes': {'type': 'RelatedModel'},
            'Id': 1
        }
        self.assertEqual(attr.load(data), RelatedModel.load({'Id': 1}))

    def test_load_many(self):
        attr = attributes.Relationship('Attr', related_model=RelatedModel, many=True)
        data = {
            'records': [
                {'attributes': {'type': 'RelatedModel'}, 'Id': 1}
            ]
        }
        self.assertEqual(attr.load(data), [RelatedModel.load({'Id': 1})])

    def test_load_when_relationship_is_none(self):
        attr = attributes.Relationship('Attr', related_model=RelatedModel)
        self.assertEqual(attr.load(None), None)

    def test_load_many_when_relationship_is_none(self):
        attr = attributes.Relationship('Attr', related_model=RelatedModel, many=True)
        self.assertEqual(attr.load(None), [])

    def test_coerce_when_relationship_is_nullable(self):
        attr = attributes.Relationship('Attr', related_model=RelatedModel, nullable=True)
        self.assertEqual(attr.coerce(None), None)

    def test_coerce_when_relationship_is_not_nullable(self):
        attr = attributes.Relationship('Attr', related_model=RelatedModel, nullable=False)
        self.assertRaises(NullSalesforceColumnError, attr.coerce, None)


class StringTest(unittest.TestCase):
    def test_coerce(self):
        attr = attributes.String('Attr')
        self.assertEqual(attr.coerce(1), '1')
        self.assertEqual(attr.coerce('1'), '1')
        self.assertEqual(attr.coerce('È'), 'È')
        self.assertRaises(NullSalesforceColumnError, attr.coerce, None)

    def test_nullable(self):
        attr = attributes.String('Attr', nullable=True)
        self.assertIsNone(attr.coerce(None))

    def test_serialize(self):
        attr = attributes.String('Attr')
        self.assertEqual(attr.serialize('1'), '1')


class IntegerTest(unittest.TestCase):
    def test_coerce(self):
        attr = attributes.Integer('Attr')
        self.assertEqual(attr.coerce('1'), 1)
        self.assertEqual(attr.coerce(1), 1)
        self.assertRaises(NullSalesforceColumnError, attr.coerce, None)

    def test_nullable(self):
        attr = attributes.Integer('Attr', nullable=True)
        self.assertIsNone(attr.coerce(None))

    def test_serialize(self):
        attr = attributes.Integer('Attr')
        self.assertEqual(attr.serialize(1), 1)


class FloatTest(unittest.TestCase):
    def test_coerce(self):
        attr = attributes.Float('Attr')
        self.assertEqual(attr.coerce('1.0'), 1.0)
        self.assertEqual(attr.coerce(1.0), 1.0)

    def test_nullable(self):
        attr = attributes.Float('Attr', nullable=True)
        self.assertIsNone(attr.coerce(None))

    def test_serialize(self):
        attr = attributes.Float('Attr')
        self.assertEqual(attr.serialize(1.1), 1.1)


class BooleanTest(unittest.TestCase):
    def test_coerce(self):
        attr = attributes.Boolean('Attr')
        self.assertEqual(attr.coerce(True), True)
        self.assertEqual(attr.coerce(False), False)
        self.assertRaises(NullSalesforceColumnError, attr.coerce, None)

    def test_nullable(self):
        attr = attributes.Boolean('Attr', nullable=True)
        self.assertIsNone(attr.coerce(None))

    def test_serialize(self):
        attr = attributes.Boolean('Attr')
        self.assertEqual(attr.serialize(True), True)


class DateTimeTest(unittest.TestCase):
    def test_coerce(self):
        attr = attributes.DateTime('Attr')

        datetime_ = datetime(year=1990, month=10, day=19, tzinfo=tzutc())
        date_ = date(year=1990, month=10, day=19)

        self.assertEqual(attr.coerce(datetime_), datetime_)
        self.assertEqual(attr.coerce(datetime_.isoformat()), datetime_)
        self.assertEqual(attr.coerce(datetime_.replace(tzinfo=None)), datetime_)
        self.assertEqual(attr.coerce(date_), datetime_)

        tz_naive_string = datetime_.replace(tzinfo=None).isoformat()
        self.assertEqual(attr.coerce(tz_naive_string), datetime_)
        self.assertRaises(NullSalesforceColumnError, attr.coerce, None)

    def test_nullable(self):
        attr = attributes.DateTime('Attr', nullable=True)
        self.assertIsNone(attr.coerce(None))

    def test_serialize(self):
        datetime_ = datetime(year=1990, month=10, day=19, tzinfo=tzutc())

        attr = attributes.DateTime('Attr')
        self.assertEqual(attr.serialize(datetime_), datetime_.isoformat())


class DateTest(unittest.TestCase):
    def test_coerce(self):
        attr = attributes.Date('Attr')

        datetime_ = datetime(year=1990, month=10, day=19, hour=5, tzinfo=tzutc())
        date_ = date(year=1990, month=10, day=19)

        self.assertEqual(attr.coerce(date_), date_)
        self.assertEqual(attr.coerce(date_.isoformat()), date_)
        self.assertEqual(attr.coerce(datetime_), date_)
        self.assertRaises(NullSalesforceColumnError, attr.coerce, None)

    def test_nullable(self):
        attr = attributes.Date('Attr', nullable=True)
        self.assertIsNone(attr.coerce(None))

    def test_serialize(self):
        date_ = date(year=1990, month=10, day=19)

        attr = attributes.Date('Attr')
        self.assertEqual(attr.serialize(date_), date_.isoformat())
