SOQL
====

.. image:: https://travis-ci.org/plangrid/soql.svg?branch=master
   :target: https://travis-ci.org/plangrid/soql
   :alt: CI Status

.. image:: https://badge.fury.io/py/soql.svg
   :target: https://badge.fury.io/py/soql
   :alt: PyPI status

|

This package provides declarative models for Salesforce objects and utilities for generating `Salesforce Object Query Language (SOQL) <https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm>`_ queries from these models.

This package works well with `Simple Salesforce <https://github.com/simple-salesforce/simple-salesforce>`_.


Usage
-----

.. code-block:: python

   from simple_salesforce import Salesforce
   from soql import attributes
   from soql import load_models_from_salesforce_data
   from soql import Model
   from soql import select


   class Account(Model):
       id = attributes.String('Id')
       deleted = attributes.Boolean('IsDeleted')
       name = attributes.String('Name')
       owner = attributes.Relationship('Owner', related_model=User)
       custom_field = attributes.String('CustomField__c', nullable=True)

   class User(Model):
       id = attributes.String('Id')
       email = attributes.String('Email')

   sf = Salesforce(...)

   query = select(Account) \
       .where(Account.id == '50130000000014c') \
       .join(Account.owner)

   resp = sf.query(str(query))

   account = load_models_from_salesforce_data(resp)[0]

   print(account.id)
   print(account.owner.id)


Models
~~~~~~

Models define in-memory representations of Salesforce object, and provide an idiomatic way to access the data.

.. code-block:: python

   from soql import attributes
   from soql import Model

   class User(Model):
       # The first argument to an attribute is its name in Salesforce.
       id = attributes.String('Id')
       email = attributes.String('Email')

   user = User(id='123', email='a@b.com')

   assert user.id == '123'

Helpers are available to load models directly from ``simple_salesforce``:

.. code-block:: python

   query = select(User)

   resp = sf.query(str(query))

   users = load_models_from_salesforce_data(resp)

Relationships can also be declared:

.. code-block:: python

   class Account(Model):
       id = attributes.String('Id')
       owner = attributes.Relationship('Owner', related_model=User)
       contacts = attributes.Relationship('Contacts', related_model=User, many=True)


Queries
~~~~~~~

SOQL queries can be generated from models:

.. code-block:: python

   from soql import select

   query = select(User).where(User.id == '123')

   assert str(query) == "SELECT User.Id, User.Email FROM User WHERE User.Id = '123'"

Most of SOQL is supported, including...

Joins:

.. code-block:: python

   from soql import select

   query = select(Account).join(Account.contacts)

   assert str(query) == "SELECT Account.Id, (SELECT User.Id, User.Email FROM Account.Contacts) FROM Account"

Subqueries:

.. code-block:: python

   from soql import select

   subquery = select(User).columns(User.email).subquery()
   query = select(User).where(User.email.in_(subquery))

   assert str(query) == "SELECT User.Id, User.Email FROM User WHERE User.Email IN (SELECT User.Email FROM User)"

And more!


Installation
------------

.. code-block::

   pip install soql


Contributing
------------

There is still work to be done, and contributions are encouraged! Check out the `contribution guide <CONTRIBUTING.rst>`_ for more information.
