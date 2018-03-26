"""
    Loaders
    ~~~~~~~

    Utilities for loading models from Salesforce API data.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import absolute_import

from soql.model_registry import model_registry


def load_model_from_salesforce_data(data):
    """
    Loads a dictionary representing a single Salesforce object into a model.

    :param dict data: data from the Salesforce API
    :rtype: admin_api_2.salesforce.orm.model.Model
    """
    object_type = data['attributes']['type']
    model = model_registry.get_by_salesforce_object_name(name=object_type)
    return model.load(data)


def load_models_from_salesforce_data(data):
    """
    Loads a dictionary representing multiple Salesforce objects into a models.

    :param dict data: data from the Salesforce API
    :rtype: list
    """
    return list(map(load_model_from_salesforce_data, data['records']))


def get_total_count(data):
    """
    Retrieves the total count from a Salesforce SOQL query.

    :param dict data: data from the Salesforce API
    :rtype: int
    """
    return data['totalSize']
