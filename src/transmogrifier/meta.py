# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from zope.component.zcml import IUtilityDirective
from zope.component.zcml import utility
from zope.configuration.fields import MessageID
from zope.configuration.fields import Path
from zope.configuration.fields import PythonIdentifier
from zope.interface import Interface

from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.interfaces import ISection
from transmogrifier.registry import configuration_registry


class IPipelineDirective(Interface):
    """Register pipeline configurations with the global registry.
    """

    name = PythonIdentifier(
        title='Name',
        description="If not specified 'default' is used.",
        default='default',
        required=False
    )

    title = MessageID(
        title='Title',
        description='Optional title for the pipeline configuration.',
        default=None,
        required=False
    )

    description = MessageID(
        title='Description',
        description='Optional description for the pipeline configuration.',
        default=None,
        required=False
    )

    configuration = Path(
        title='Configuration',
        description='The pipeline configuration file to register.',
        required=True
    )


class IBlueprintDirective(IUtilityDirective):
    """Section blueprint
    """


def pipeline(_context, configuration,
             name='default', title=None, description=None):
    """Register new pipeline into the global registry
    """
    if title is None:
        title = "Pipeline configuration '{0:s}'".format(name)

    if description is None:
        description = ''

    _context.action(
        discriminator=('pipeline', name),
        callable=configuration_registry.registerConfiguration,
        args=(name, title, description, configuration))


def blueprint(_context, provides=ISectionBlueprint, component=None,
              factory=None, permission=None, name=''):
    assert ISection in component.__implemented__
    utility(_context, provides=provides, component=component,
            factory=factory, permission=permission, name=name)
