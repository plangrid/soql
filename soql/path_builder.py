"""
    Path Builder
    ~~~~~~~~~~~~

    Helper for building relationship queries.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import absolute_import

from soql.attributes import Relationship
from soql.nodes import ColumnPath
from soql.utils import to_unicode


class PathBuilder(object):
    """
    Tracks chained model-relationship references and exposes helper methods
    for interpreting the chain.
    """
    def __init__(self, model, path=None):
        """
        El constructor.

        :param admin_api_2.salesforce.orm.model.Model model:
        :param list path: Optionally instantiate the instance with an existing
            path. This is useful when chaining relationships.
        """
        self.model = model
        self.path = path or []

    def _iterate_path(self, path_index):
        """
        Iterates through the path, starting from the base model to the last
        relationship reference.

        This yields tuples of the relationship's model and the attribute
        for the relationship.

        For example, if we had.....


            relationship = attributes.Relationship('Parent')

            class SomeModel(Model):
                id = attributes.String('Id')
                parent = relationship

            path_builder = PathBuilder(SomeModel)\
                .extend_path(parent)\
                .extend_path(parent)

        This would yield.....

            (SomeModel, relationship)
            (SomeModel, relationship)

        :param integer path_index: Only iterate up to this point in the path.
            Use -1 to iterate over the entire path.
        """
        if path_index == -1:
            # -1 + 1 = 0... but -1 means we want to iterate through the entire
            # path, so we'll check for this special case.
            inclusive_index = None
        else:
            inclusive_index = path_index + 1

        last_model = self.model

        for relationship in self.path[0:inclusive_index]:
            model_relationship = last_model.declared_attrs[relationship]
            last_model = model_relationship.related_model
            yield last_model, model_relationship

    def _build_soql_column_path(self):
        """This builds the SOQL representation of this path."""
        # The column path starts with the name of the original object
        path = [self.model.__soql_name__()]

        for _, attr in self._iterate_path(path_index=-1):
            path.append(attr.salesforce_name)

        return path

    def get_model_in_path(self, path_index):
        """Get the model of a certain point in the relationship path."""
        last_model = self.model
        for model, _ in self._iterate_path(path_index=path_index):
            last_model = model
        return last_model

    def get_relationship_attr_in_path(self, path_index):
        """Get the relationship attribute of a certain point in the
        relationship path."""
        last_model_relationship_attr = None
        for _, attr in self._iterate_path(path_index=path_index):
            last_model_relationship_attr = attr
        return last_model_relationship_attr

    def get_column_node(self):
        """Builds a Node representing this path."""
        return ColumnPath(*self._build_soql_column_path())

    def get_last_model_column_nodes(self):
        """Returns SOQL representations of all the columns for the final
        model in the relationship path."""
        last_model = self.get_model_in_path(path_index=-1)
        return [
            ColumnPath(self.extend_path(attr))
            for attr in last_model.iter_columns()
        ]

    def extend_path(self, item):
        """Extends the path with another reference.

        If that reference is another relationship, this returns a new instance.

        If that reference is column, we've reached the end of our path, and this
        returns a Colum node.
        """
        last_model = self.get_model_in_path(path_index=-1)
        attr = last_model.declared_attrs[item]

        if isinstance(attr, Relationship):
            # Looks like someone is requesting another relationship, so we'll
            # keep extending the chain!
            return PathBuilder(
                model=self.model,
                path=self.path + [item]
            )

        # Looks like someone is requesting a column, which is a leaf in a path,
        # so we'll return a column node.
        path = self._build_soql_column_path() + [attr.salesforce_name]
        return ColumnPath(*path)

    def __getattr__(self, item):
        """
        This little bit of magic let's us do things like...

            select(SomeModel).where(SomeModel.relationship.name == 'BLAM!')
        """
        return self.extend_path(item=item)

    def __unicode__(self):
        return to_unicode(self.get_column_node())

    def __str__(self):
        return str(self.get_column_node())
