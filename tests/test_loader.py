import unittest

from soql import attributes
from soql import Model
from soql import ModelNotRegistered
from soql import load_model_from_salesforce_data
from soql import load_models_from_salesforce_data
from soql import get_total_count


class ModelBase(Model):
    __abstract__ = True
    id = attributes.Integer('Id')


class LoadedToMany(ModelBase):
    __salesforce_object_name = 'LoadedToMany__c'


class LoadedToOne(ModelBase):
    __salesforce_object_name__ = 'LoadedToOne__c'


class Loaded(ModelBase):
    id = attributes.Integer('Id')
    one = attributes.Relationship('One', related_model=LoadedToOne)
    many = attributes.Relationship('Many', related_model=LoadedToMany, many=True)


class LoaderTest(unittest.TestCase):
    def format_dict_as_api_data(self, data, object_type):
        formatted = {
            'attributes': {'type': object_type},
        }
        formatted.update(data)
        return formatted

    def format_collection_as_api_data(self, collection, object_type):
        formatted = {
            'totalSize': len(collection),
            'records': [
                self.format_dict_as_api_data(data=o, object_type=object_type)
                for o in collection
            ]
        }
        return formatted

    def test_load_model_from_salesforce_data(self):
        one = self.format_dict_as_api_data(
            data={'Id': 1},
            object_type=LoadedToOne.__soql_name__()
        )
        many = self.format_collection_as_api_data(
            collection=[{'Id': 2}, {'Id': 3}],
            object_type=LoadedToMany.__soql_name__()
        )
        data = self.format_dict_as_api_data(
            data={'Id': 4, 'One': one, 'Many': many},
            object_type=Loaded.__soql_name__()
        )
        loaded = load_model_from_salesforce_data(data=data)

        self.assertEqual(
            loaded,
            Loaded(
                id=4,
                one=LoadedToOne(id=1),
                many=[LoadedToMany(id=2), LoadedToMany(id=3)]
            )
        )

    def test_load_models_from_salesforce_data(self):
        one = self.format_dict_as_api_data(
            data={'Id': 1},
            object_type=LoadedToOne.__soql_name__()
        )
        many = self.format_collection_as_api_data(
            collection=[{'Id': 2}, {'Id': 3}],
            object_type=LoadedToMany.__soql_name__()
        )
        data = self.format_collection_as_api_data(
            collection=[{'Id': 4, 'One': one, 'Many': many}],
            object_type=Loaded.__soql_name__()
        )
        loaded = load_models_from_salesforce_data(data=data)

        self.assertEqual(
            loaded,
            [
                Loaded(
                    id=4,
                    one=LoadedToOne(id=1),
                    many=[LoadedToMany(id=2), LoadedToMany(id=3)]
                )
            ]
        )

    def test_get_total_count(self):
        data = self.format_collection_as_api_data(
            collection=[{'Id': 1}, {'Id': 2}],
            object_type=Loaded.__soql_name__()
        )
        self.assertEqual(get_total_count(data=data), 2)

    def test_abstract_models_are_ignored(self):
        data = self.format_dict_as_api_data(
            data={'Id': 1},
            object_type=ModelBase.__soql_name__()
        )

        with self.assertRaises(ModelNotRegistered):
            load_model_from_salesforce_data(data=data)
