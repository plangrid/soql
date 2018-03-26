import unittest
from datetime import date, datetime

from dateutil.tz import tzutc

from soql import attributes
from soql import Model
from soql import AttributeNotSet
from soql import AttributeNotLoaded
from soql import ExpectedColumnMissing
from soql.model import UNLOADED
from soql.model import UNSET


class AParent(Model):
    id = attributes.Integer('Id')
    name = attributes.String('Name')
    age = attributes.Integer('Age')


class AChild(Model):
    id = attributes.Integer('Id')
    name = attributes.String('Name')
    mom = attributes.Relationship('Mom', related_model=AParent)


class AllZeTypes(Model):
    id = attributes.Integer('Id')
    name = attributes.String('Name')
    price = attributes.Float('Price')
    start_date = attributes.Date('StartDate')
    created_time = attributes.DateTime('CreatedTime')


class AllZeRelationships(Model):
    parent = attributes.Relationship('Parent', related_model=AParent)
    children = attributes.Relationship('Children', related_model=AChild, many=True)


class ModelTest(unittest.TestCase):
    def test_loading_from_salesforce_api_data(self):
        start_date = date(year=1990, month=10, day=19)
        created_time = datetime(year=1990, month=10, day=19, tzinfo=tzutc())

        instance = AllZeTypes.load({
            'attributes': {'type': 'AllZeTypes'},
            'Id': '123',
            'Name': 11,
            'Price': '3.50',
            'StartDate': str(start_date),
            'CreatedTime': created_time.isoformat()
        })
        self.assertEqual(instance.id, 123)
        self.assertEqual(instance.name, '11')
        self.assertEqual(instance.price, 3.50)
        self.assertEqual(instance.start_date, start_date)
        self.assertEqual(instance.created_time, created_time)

        instance = AllZeRelationships.load({
            'Children': {
                'records': [
                    {'attributes': {'type': 'AChild'}, 'Id': 123, 'Name': 'Jack'},
                    {'attributes': {'type': 'AChild'}, 'Id': 456, 'Name': 'Jill'}
                ]
            }
        })
        self.assertEqual(instance.children, [
            AChild(id=123, name='Jack', mom=UNLOADED),
            AChild(id=456, name='Jill', mom=UNLOADED)
        ])
        self.assertRaises(AttributeNotLoaded, lambda: instance.parent)

        instance = AllZeRelationships.load({
            'Parent': {
                'attributes': {'type': 'AParent'},
                'Id': 123,
                'Name': 'Jack',
                'Age': 45}
        })
        self.assertEqual(instance.parent, AParent(id=123, name='Jack', age=45))
        self.assertRaises(AttributeNotLoaded, lambda: instance.children)

        # Assert loading hard fails if a column is missing
        with self.assertRaises(ExpectedColumnMissing):
            instance = AllZeTypes.load({
                'attributes': {'type': 'AllZeTypes'},
                'Id': '123',
                'Name': 11,
            })

    def test_instantiation(self):
        start_date = date(year=1990, month=10, day=19)
        created_time = datetime(year=1990, month=10, day=19, tzinfo=tzutc())

        instance = AllZeTypes(
            id=123,
            name='11',
            price=3.50,
            start_date=start_date,
            created_time=created_time
        )
        self.assertEqual(instance.id, 123)
        self.assertEqual(instance.name, '11')
        self.assertEqual(instance.price, 3.50)
        self.assertEqual(instance.start_date, start_date)
        self.assertEqual(instance.created_time, created_time)

        instance = AllZeRelationships(
            children=[AChild(id=123, name='Jack')]
        )
        self.assertEqual(instance.children, [
            AChild(id=123, name='Jack', mom=UNSET)
        ])
        self.assertRaises(AttributeNotSet, lambda: instance.parent)

        instance = AllZeRelationships(
            parent=AParent(id=123, name='Jack', age=45)
        )
        self.assertEqual(instance.parent, AParent(id=123, name='Jack', age=45))
        self.assertRaises(AttributeNotSet, lambda: instance.children)

    def test_multiple_inheritance(self):
        class Preferences(Model):
            candy = attributes.String('Candy')

        class FavoriteChild(AChild, Preferences):
            pass

        favorite_child = FavoriteChild(
            id=123,
            name='Jennifer',
            candy='twizzlers'
        )

        self.assertEqual(favorite_child.id, 123)
        self.assertEqual(favorite_child.name, 'Jennifer')
        self.assertEqual(favorite_child.candy, 'twizzlers')

    def test_back_references(self):
        class Foo(Model):
            bar = attributes.Relationship('Bar', related_model='Bar')

        class Bar(Model):
            foos = attributes.Relationship('Foos', related_model=Foo, many=True)

        bar = Bar()
        foo = Foo(bar=bar)
        self.assertEqual(foo.bar, bar)

        foos = [Foo() for _ in range(3)]
        bar = Bar(foos=foos)
        self.assertEqual(bar.foos, foos)

    def test_set_attributes(self):
        child = AChild(id=456, name='Jill')
        child.name = 'MOTHA FUCKIN JILL'
        self.assertEqual(child.name, 'MOTHA FUCKIN JILL')

    def test_changes(self):
        start_date = date(year=1990, month=10, day=19)
        new_date = date(year=1990, month=10, day=20)

        instance = AllZeTypes(id=456, name='Jill', start_date=start_date)

        self.assertEqual(instance.changes(), {})

        instance.name = 'Bill'

        self.assertEqual(instance.changes(), {
            'Name': 'Bill'
        })

        # Test that the value is coerced
        instance.start_date = new_date

        self.assertEqual(instance.changes(), {
            'StartDate': new_date.isoformat(),
            'Name': 'Bill'
        })

        instance.reset_instance_state()

        self.assertEqual(instance.changes(), {})

        # No changes!
        instance.name = 'Bill'

        self.assertEqual(instance.changes(), {})

        instance.name = 'Jill'

        self.assertEqual(instance.changes(), {
            'Name': 'Jill'
        })
