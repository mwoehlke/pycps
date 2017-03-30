#==============================================================================
class LanguageOptions(object):
    options = []

    #--------------------------------------------------------------------------
    def __init__(self, json_data, prefix=None):
        self.options = json_data

        if prefix is not None:
            pass # TODO resolve for all values

    #--------------------------------------------------------------------------
    def __repr__(self):
        return repr(self.options)

    #--------------------------------------------------------------------------
    def __getitem__(self, language):
        if type(self.options) is dict:
            return _get(language, self.options, [])

        return self.options

#==============================================================================
class Configuration(object):
    compile_features = None
    compile_flags = None
    definitions = None
    includes = None
    link_features = None
    link_flags = None
    link_languages = ['C']
    link_libraries = []
    location = None
    link_location = None
    requires = []

    #--------------------------------------------------------------------------
    def __init__(self, json_data, prefix, parent=None):
        def make_language_options(key, json_data, *args):
            return _make(LanguageOptions, key, json_data, *args)

        def get_or_inherit(key, getter, *args):
            attr = key.replace('-', '_')
            value = getter(key, json_data, *args)
            if value is None and parent is not None:
                value = getattr(parent, attr)
            if value is None:
                value = getattr(self, attr)
            setattr(self, attr, value)

        get_or_inherit('compile-features', make_language_options)
        get_or_inherit('compile-flags', make_language_options)
        get_or_inherit('definitions', make_language_options)
        get_or_inherit('includes', make_language_options, prefix)
        get_or_inherit('link-features', make_language_options)
        get_or_inherit('link-flags', make_language_options)
        get_or_inherit('link-languages', _get)
        get_or_inherit('link-libraries', _get)
        get_or_inherit('location', _get)
        get_or_inherit('link-location', _get)
        get_or_inherit('requires', _get)

        if self.link_location is None:
            self.link_location = self.location

    #--------------------------------------------------------------------------
    def __repr__(self):
        return repr(self.__dict__)

#==============================================================================
class Component(Configuration):
    kind = None
    configurations = {}

    #--------------------------------------------------------------------------
    def __init__(self, json_data, prefix):
        super(Component, self).__init__(json_data, prefix)

        self.kind = _get('type', json_data)

        configurations = {}
        for cn, cd in _get('configurations', json_data, {}).iteritems():
            configurations[cn] = Configuration(cd, prefix, self)
        self.configurations = configurations

#==============================================================================
class Requirement(object):
    pass # TODO

#==============================================================================
class Platform(object):
    isa = None
    kernel = None
    c_runtime = None
    cpp_runtime = None
    clr = None
    jvm = None

    #==========================================================================
    class Runtime(object):
        vendor = None
        version = None

        def __init__(self, language, json_data):
            self.vendor = _get('%s-vendor' % language, json_data)
            self.version = _get('%s-version' % language, json_data)

        def __repr__(self):
            return repr(self.__dict__)

    #--------------------------------------------------------------------------
    def __init__(self, json_data):
        self.isa = _get('isa', json_data)
        self.kernel = _get('kernel', json_data)
        self.c_runtime = Platform.Runtime('c-runtime', json_data)
        self.cpp_runtime = Platform.Runtime('cpp-runtime', json_data)
        self.clr = Platform.Runtime('clr', json_data)
        self.jvm = Platform.Runtime('jvm', json_data)

    #--------------------------------------------------------------------------
    def __repr__(self):
        return repr(self.__dict__)

#==============================================================================
class Package(object):
    name = None
    platform = None
    version = None
    compat_version = None
    configurations = []
    components = {}
    default_components = []
    requires = {}

    #--------------------------------------------------------------------------
    def __init__(self, path, json_data):
        import os

        self.name = _get('name', json_data)
        self.platform = _make(Platform, 'platform', json_data)
        self.version = _get('version', json_data)
        self.compat_version = _get('compat-version', json_data)
        self.configurations = _get('configurations', json_data, [])
        self.default_components = _get('default-components', json_data, [])

        if path is not None:
            cps_path = _get('cps-path', json_data, '')
            prefix = '@prefix@' # FIXME
        else:
            prefix = '@prefix@'

        components = {}
        for cn, cd in _get('components', json_data, {}).iteritems():
            components[cn] = Component(cd, prefix)
        self.components = components

        # TODO requires

        if self.compat_version is None:
            self.compat_version = self.version

    #--------------------------------------------------------------------------
    def __repr__(self):
        return repr(self.__dict__)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#------------------------------------------------------------------------------
def _get(key, json_data, default=None):
    key = key.lower()
    for jk, jv in json_data.iteritems():
        if jk.lower() == key:
            return jv if jv is not None else default

    return default

#------------------------------------------------------------------------------
def _make(constructor, key, json_data, *args):
    json_data = _get(key, json_data)
    if json_data is not None:
        return constructor(json_data, *args)

    return None

#------------------------------------------------------------------------------
def read(filepath, canonicalize=True):
    import json
    import os

    if canonicalize:
        path = os.path.abspath(os.path.dirname(filepath))
    else:
        path = None

    json_data = json.load(open(filepath))
    return Package(path, json_data)

#------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    print read(sys.argv[1])
