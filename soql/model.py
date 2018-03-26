"""
    Model
    ~~~~~

    Base class for declarative models.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

from __future__ import absolute_import
from collections import OrderedDict
from copy import copy

from six import with_metaclass

from soql.attributes import AttributeBase
from soql.attributes import Column
from soql.attributes import Relationship
from soql.model_registry import model_registry
from soql.path_builder import PathBuilder


class UNLOADED(object):
    """Placeholder for a model attribute value for data that was never loaded
    from the API."""
    pass


class UNSET(object):
    """Placeholder for a model attribute value for data that was never set."""
    pass


class AttributeNotLoaded(Exception):
    pass


class AttributeNotSet(Exception):
    pass


class ExpectedColumnMissing(Exception):
    pass


class _ModelMeta(type):
    """
    Turns boring classes into magical, declarative style models!
    """
    def __new__(mcs, name, bases, cls_attrs):
        """
        Metaclasses are classes for classes... which means this method is
        responsible for creating a new class. That means we can hijack the
        class declaration to do magical things...

        :param name: The name of the class being declared
        :param bases: The base classes the class is being declared with
        :param cls_attrs: A dictionary of attributes the class is being declared with
        :return: the new class
        """
        # This handles inheritance by crawling through all the base classes
        # and grabbing their declared attributes.
        inherited_attributes = OrderedDict()
        for base_ in bases:
            if hasattr(base_, 'declared_attrs'):
                inherited_attributes.update(
                    copy(getattr(base_, 'declared_attrs')))

        # Find any attributes that are declared in the model.
        # It helps testability tremendously if the attributes come in a reliable
        # order... hence the sorting and OrderedDict
        attributes = OrderedDict()
        for key in sorted(cls_attrs.keys()):
            if isinstance(cls_attrs[key], AttributeBase):
                attributes[key] = cls_attrs[key]

        # Pop them out of the attribute dictionary so they don't get declared
        # as normal attributes....
        for key, attr in attributes.items():
            cls_attrs.pop(key)

        # Now that the attributes have been pruned, we can create the class
        klass = super(_ModelMeta, mcs).__new__(mcs, name, bases, cls_attrs)

        # We'll attach those attributes, along with the attributes from the
        # inherited classes, to a single attribute.
        setattr(klass, 'declared_attrs', OrderedDict())
        klass.declared_attrs.update(inherited_attributes)
        klass.declared_attrs.update(attributes)

        # Finally, register the model in the model registry.
        if not cls_attrs.get('__abstract__'):
            model_registry.add(klass)

        return klass

    def __getattr__(self, item):
        """
        This little bit of magic helps us do things like:

            select(SomeModel).where(SomeModel.name == 'BLAM!')

        While still having instances of the model return the attribute's value:

            assert SomeModel().name == 'BLAM!'

        (Note - because this is a meta class, "self" is the model)
        """
        if item not in self.declared_attrs:
            raise AttributeError("{} has no attribute '{}'".format(self, item))

        return PathBuilder(model=self).extend_path(item=item)


class Model(with_metaclass(_ModelMeta)):
    """
    Declarative style models!

    Example usage:

        class SomeSalesforceObject(Model):
            # Optionally specify the name of the object as known by Salesforce.
            # This defaults to the class name.
            __salesforce_object_name__ = 'UglyAssName__c'

            id = attributes.String('Id')
            name = attributes.String('Name')

        instance = SomeSalesforceObject(id='123', name='BLAM!')
        assert instance.id == '123'
    """
    def __init__(self, **kwargs):
        """
        Constructs an instance of the Model.

        :param kwargs: attributes to set on the instance. These should map to
            the model attribute names, NOT the names as known by Salesforce.
        """
        self._instance_attrs = {}
        self._changed_attrs = set()

        # Crawl through the attributes declared in the class, pulling them
        # out of the provided kwargs and setting them as instance attributes.
        for key, attr in self.declared_attrs.items():
            if key not in kwargs:
                self._instance_attrs[key] = UNSET
            elif kwargs[key] is UNLOADED:
                self._instance_attrs[key] = UNLOADED
            else:
                self._instance_attrs[key] = attr.coerce(kwargs[key])

    def __getattr__(self, item):
        """
        Any attempts to retrieve to an attribute that doesn't seem to exist
        is redirected to the the model's mapped attributes.
        """
        if item not in self._instance_attrs:
            raise AttributeError("{} has no attribute '{}'".format(self, item))

        value = self._instance_attrs[item]
        if value is UNLOADED:
            raise AttributeNotLoaded(item)
        if value is UNSET:
            raise AttributeNotSet(item)
        return value

    def __setattr__(self, key, value):
        if key == '_instance_attrs' or key not in self._instance_attrs:
            super(Model, self).__setattr__(key, value)
        elif isinstance(self.__class__.declared_attrs[key], Relationship):
            super(Model, self).__setattr__(key, value)
        else:
            coerced = self.__class__.declared_attrs[key].coerce(value)
            if coerced != getattr(self, key):
                self._changed_attrs.add(key)

            self._instance_attrs[key] = coerced

    def __eq__(self, other):
        """
        Compares a model instance to another model instance.

        :param other: the other model instance being compared
        :rtype: bool
        """
        if not isinstance(other, self.__class__):
            return False
        return self._instance_attrs == other._instance_attrs

    @classmethod
    def __soql_name__(cls):
        """
        Returns the name of the model, as known by Salesforce.

        :rtype: str
        """
        return getattr(cls, '__salesforce_object_name__', cls.__name__)

    @classmethod
    def iter_columns(cls):
        """
        Iterates over the column attributes of a model (ignoring nasty things
        like relationships. Yuck.).
        """
        for key, attr in cls.declared_attrs.items():
            if isinstance(attr, Column):
                yield key

    @classmethod
    def load(cls, data):
        """
        Constructs an instance of the Model from Salesforce API data.

        :param dict data: dictionary of data coming straight from the
            Salesforce API.
        :rtype: admin_api_2.salesforce.orm.model.Model
        """
        attrs = {}
        for key, attr in cls.declared_attrs.items():
            if isinstance(attr, Column) and attr.salesforce_name not in data:
                # Hard fail if we were expecting a column from the API and
                # it didn't show up
                msg = "Expected {} for model {}. Didn't find that in: {}" \
                      "".format(attr.salesforce_name, cls, data)
                raise ExpectedColumnMissing(msg)
            elif isinstance(attr, Relationship) and attr.salesforce_name not in data:
                # Relationships, on the other hand, have to be explicitly
                # joined and its ok for them to be missing.
                attrs[key] = UNLOADED
            else:
                attrs[key] = attr.load(data[attr.salesforce_name])

        return cls(**attrs)

    def changes(self):
        model = self.__class__

        changes = {}
        for key in self._changed_attrs:
            attr = model.declared_attrs[key]
            value = attr.serialize(getattr(self, key))
            changes[attr.salesforce_name] = value

        return changes

    def reset_instance_state(self):
        self._changed_attrs = set()
