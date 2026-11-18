# -*- coding: utf-8 -*-

from archetypes.schemaextender.field import ExtensionField
from Products.Archetypes.public import StringField


class ExtStringField(ExtensionField, StringField):
    """Extended String Field
    """
