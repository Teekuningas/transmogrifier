import os
import shutil
import tempfile
import unittest
import operator
from zope.interface import classImplements
from zope.component import provideUtility
from zope.testing import doctest, cleanup
from Products.Five import zcml

import collective.transmogrifier
from collective.transmogrifier.transmogrifier import configuration_registry
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

# Unit tests

class MetaDirectivesTests(unittest.TestCase):
    def setUp(self):
        zcml.load_config('meta.zcml', collective.transmogrifier)
        
    def tearDown(self):
        configuration_registry.clear()
        cleanup.cleanUp()
        
    def testEmptyZCML(self):
        zcml.load_string('''\
<configure xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier">
</configure>''')
        self.assertEqual(configuration_registry.listConfigurationIds(), ())
    
    def testConfigZCML(self):
        zcml.load_string('''\
<configure
    xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier"
    i18n_domain="collective.transmogrifier">
<transmogrifier:registerConfig
    name="collective.transmogrifier.tests.configname"
    title="config title"
    description="config description"
    configuration="filename.cfg"
    />
</configure>''')
        self.assertEqual(configuration_registry.listConfigurationIds(),
                         (u'collective.transmogrifier.tests.configname',))
        path = os.path.split(collective.transmogrifier.__file__)[0]
        self.assertEqual(
            configuration_registry.getConfiguration(
                 u'collective.transmogrifier.tests.configname'),
            dict(id=u'collective.transmogrifier.tests.configname',
                 title=u'config title',
                 description=u'config description',
                 configuration=os.path.join(path, 'filename.cfg')))
    
    def testConfigZCMLDefaults(self):
        zcml.load_string('''\
<configure
    xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier"
    i18n_domain="collective.transmogrifier">
<transmogrifier:registerConfig
    name="collective.transmogrifier.tests.configname"
    configuration="filename.cfg"
    />
</configure>''')
        self.assertEqual(configuration_registry.listConfigurationIds(),
                         (u'collective.transmogrifier.tests.configname',))
        path = os.path.split(collective.transmogrifier.__file__)[0]
        self.assertEqual(
            configuration_registry.getConfiguration(
                u'collective.transmogrifier.tests.configname'),
            dict(id=u'collective.transmogrifier.tests.configname',
                 title=u'Pipeline configuration '
                       u"'collective.transmogrifier.tests.configname'",
                 description=u'',
                 configuration=os.path.join(path, 'filename.cfg')))
    

class OptionSubstitutionTests(unittest.TestCase):
    def _loadOptions(self, opts):
        from collective.transmogrifier.transmogrifier import Transmogrifier
        tm = Transmogrifier(object())
        tm._raw = opts
        tm._data = {}
        return tm
        
    def testNoSubs(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='python'),
                eggs=dict(foo='bar'),
            ))
        self.assertEqual(opts['spam']['monty'], 'python')
        self.assertEqual(opts['eggs']['foo'], 'bar')
        
    def testSimpleSub(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='python'),
                eggs=dict(foo='${spam:monty}'),
            ))
        self.assertEqual(opts['spam']['monty'], 'python')
        self.assertEqual(opts['eggs']['foo'], 'python')
    
    def testSkipTALESStringExpressions(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='string:${spam/eggs}'),
                eggs=dict(foo='${spam/monty}')
            ))
        self.assertEqual(opts['spam']['monty'], 'string:${spam/eggs}')
        self.assertRaises(ValueError, operator.itemgetter('eggs'), opts)
        
    def testErrors(self):
        opts = self._loadOptions(
            dict(
                empty=dict(),
                spam=dict(monty='${eggs:foo}'),
                eggs=dict(foo='${spam:monty}'),
            ))
        self.assertRaises(ValueError, operator.itemgetter('spam'), opts)
        self.assertRaises(KeyError, operator.itemgetter('dontexist'), opts)
        self.assertRaises(KeyError, operator.itemgetter('dontexist'),
                          opts['empty'])
        
class ConstructPipelineTests(cleanup.CleanUp, unittest.TestCase):
    def _doConstruct(self, transmogrifier, sections, pipeline=None):
        from collective.transmogrifier.utils import constructPipeline
        return constructPipeline(transmogrifier, sections, pipeline)
    
    def testNoISection(self):
        config = dict(
            noisection=dict(
                blueprint='collective.transmogrifier.tests.noisection'))
        
        class NotAnISection(object):
            def __init__(self, transmogrifier, name, options, previous):
                self.previous = previous
            def __iter__(self):
                for item in self.previous:
                    yield item
        
        provideUtility(NotAnISection, ISectionBlueprint,
                       name=u'collective.transmogrifier.tests.noisection')
        self.assertRaises(ValueError, self._doConstruct,
                          config, ['noisection'])
        
        classImplements(NotAnISection, ISection)
        # No longer raises
        self._doConstruct(config, ['noisection'])

# Doctest support

BASEDIR = None

def registerConfig(name, configuration):
    filename = os.path.join(BASEDIR, '%s.cfg' % name)
    open(filename, 'w').write(configuration)
    configuration_registry.registerConfiguration(
        name,
        u"Pipeline configuration '%s' from "
        u"'collective.transmogrifier.tests'" % name,
        u'', filename)

def setUp(test):
    global BASEDIR
    BASEDIR = tempfile.mkdtemp('transmogrifierTestConfigs')
    
    class PloneSite(object):
        def Title(self):
            return u'Plone Test Site'
    
    test.globs.update(dict(
        registerConfig=registerConfig,
        ISectionBlueprint=ISectionBlueprint,
        ISection=ISection,
        plone=PloneSite(),
        ))

def tearDown(test):
    from collective.transmogrifier import transmogrifier
    transmogrifier.configuration_registry.clear()
    shutil.rmtree(BASEDIR)
    cleanup.cleanUp()

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MetaDirectivesTests),
        unittest.makeSuite(OptionSubstitutionTests),
        unittest.makeSuite(ConstructPipelineTests),
        doctest.DocFileSuite(
            'transmogrifier.txt',
            setUp=setUp, tearDown=tearDown),
    ))
