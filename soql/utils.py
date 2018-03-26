"""
    Utilities
    ~~~~~~~~~

    Random helpers.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import sys


class AttrDict(dict):
    """This is just a little convenience class to make dealing with
    static sets prettier."""
    def __getattr__(self, attr):
        return self[attr]


if sys.version_info[0] < 3:
    to_unicode = unicode
else:
    to_unicode = str
