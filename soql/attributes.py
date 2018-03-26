"""
    Attributes
    ~~~~~~~~~~

    Attributes for declarative models.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import absolute_import
from datetime import datetime, date

from dateutil.parser import parse
from dateutil.tz import tzutc

from soql.model_registry import model_registry
from soql.loaders import load_models_from_salesforce_data
from soql.loaders import load_model_from_salesforce_data


class NullSalesforceColumnError(Exception):
    def __init__(self, attribute):
        self.attribute = attribute
        msg = '{attribute} is unexpectedly null'.format(
            attribute=attribute.salesforce_name,
        )
        super(NullSalesforceColumnError, self).__init__(msg)


class AttributeBase(object):
    def __init__(self, salesforce_name, nullable=False):
        """
        Base Attribute class for declarative models.

        :param str salesforce_name: This should be the attribute name as it
            is in Salesforce. The ORM will use this when loading data from
            the API and for compiling SOQL statements.
        :param bool nullable: If True, this field can be None.
        """
        self.salesforce_name = salesforce_name
        self.nullable = nullable

    def load(self, value):
        """
        This is called when loading data from the Salesforce API, and can be
        used to pre process data before coercion.

        :param value: the attribute value coming from Salesforce (note - this
            value will have already been JSON loaded)
        :return: the processed value.
        """
        return value

    def coerce(self, value):
        """
        This is called on model instantiation and is used to coerce the value
        to the attribute's type.

        :param value: the pre-processed attribute value.
        :return: the coerced value.
        """
        if self.nullable and value is None:
            return value
        if not self.nullable and value is None:
            raise NullSalesforceColumnError(attribute=self)
        else:
            return self._coerce(value=value)

    def _coerce(self, value):
        return value


class Relationship(AttributeBase):
    def __init__(self, salesforce_name, related_model, many=False):
        """
        This special attribute represents a relationship to another model.

        :param salesforce_name:
        :param admin_api_2.salesforce.orm.model.Model|str related_model: The
            object type this is a relationship to. The Model itself or a string
            can be used - the latter of which allows for circular references.
        :param many: If False (default), this represents a many-to-one
            relationship. If True, this represents a one-to-many relationship.
        """
        super(Relationship, self).__init__(salesforce_name=salesforce_name)
        self._related_model = related_model
        self.many = many

    @property
    def related_model(self):
        if isinstance(self._related_model, str):
            # Looks like the related model is a string.... that's ok, as it
            # allows for back references. Fetch the model from the registry.
            return model_registry.get_by_model_name(self._related_model)
        return self._related_model

    def load(self, value):
        if self.many and value is None:
            return []
        if self.many:
            return load_models_from_salesforce_data(data=value)
        if value is None:
            return None
        return load_model_from_salesforce_data(data=value)


class Column(AttributeBase):
    def serialize(self, value):
        return value


class String(Column):
    def _coerce(self, value):
        try:
            return str(value)
        except UnicodeEncodeError:
            return value


class Integer(Column):
    def _coerce(self, value):
        return int(value)


class Float(Column):
    def _coerce(self, value):
        return float(value)


class Boolean(Column):
    def _coerce(self, value):
        return bool(value)


class Date(Column):
    def _coerce(self, value):
        if isinstance(value, datetime):
            return date(
                year=value.year,
                month=value.month,
                day=value.day
            )
        if isinstance(value, date):
            return value
        else:
            dt = parse(value)
            return date(
                year=dt.year,
                month=dt.month,
                day=dt.day
            )

    def serialize(self, value):
        return value.isoformat()


class DateTime(Column):
    def _coerce(self, value):
        if isinstance(value, datetime):
            if not value.tzinfo:
                # Assume timezone naive datetimes are UTC
                return value.replace(tzinfo=tzutc())
            return value
        if isinstance(value, date):
            return datetime(
                year=value.year,
                month=value.month,
                day=value.day,
                tzinfo=tzutc()
            )
        else:
            return self.coerce(parse(value))

    def serialize(self, value):
        return value.isoformat()
