"""
    Model Registry
    ~~~~~~~~~~~~~~

    Global registry for models.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

class ModelAlreadyRegistered(Exception):
    pass


class ModelNotRegistered(Exception):
    pass


class ModelRegistry(object):
    """A simple store for all models that have been declared."""

    def __init__(self):
        # To avoid O(n) lookups, We'll maintain a mapping from the model's
        # class name to the model AND a mapping from the model's associated
        # Saleforce object name to the model.
        self._registry_by_sf_obj_name = {}
        self._registry_by_model_name = {}

    def add(self, model):
        """
        Adds a model to the store.

        :param admin_api_2.salesforce.orm.model.Model model:
        """
        salesforce_object_name = model.__soql_name__()
        model_name = model.__name__

        if salesforce_object_name in self._registry_by_sf_obj_name:
            raise ModelAlreadyRegistered(
                'Salesforce object name: {}'.format(salesforce_object_name)
            )
        if model_name in self._registry_by_model_name:
            raise ModelAlreadyRegistered(
                'Model name: {}'.format(model_name)
            )

        self._registry_by_sf_obj_name[salesforce_object_name] = model
        self._registry_by_model_name[model_name] = model

    def get_by_salesforce_object_name(self, name):
        """
        Retrieves a model from the registry with the object's name as known
        by Salesforce.

        :param str name:
        :rtype: admin_api_2.salesforce.orm.model.Model
        """
        if name not in self._registry_by_sf_obj_name:
            raise ModelNotRegistered('Salesforce object name: {}'.format(name))
        return self._registry_by_sf_obj_name[name]

    def get_by_model_name(self, name):
        """
        Retrieves a model from the registry with model's class name.

        :param str name:
        :rtype: admin_api_2.salesforce.orm.model.Model
        """
        if name not in self._registry_by_model_name:
            raise ModelNotRegistered('Model name: {}'.format(name))
        return self._registry_by_model_name[name]


model_registry = ModelRegistry()
