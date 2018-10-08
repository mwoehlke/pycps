import sys

import semantic_version as sv

# Compatibility, without depending on `six`.
if sys.version_info.major >= 3:
    iteritems = dict.items
    unicode = str
    def map(f, xs): return [f(x) for x in xs]
else:
    iteritems = dict.iteritems

current_version_info = [0, 8, 0]
current_version = ".".join(map(str, current_version_info))
supported_cps_versions = sv.Spec('>=0.6.0,<=%s' % current_version)

#==============================================================================
class Object(object):
    #--------------------------------------------------------------------------
    def __init__(self, json_data, prefix=None):
        self.data = json_data
        self.extensions = {}

        for key, value in iteritems(json_data):
            if key.lower().startswith('x-'):
                self.extensions[key] = value

    #--------------------------------------------------------------------------
    def __repr__(self):
        return repr(self.__dict__)

#==============================================================================
class LanguageOptions(object):
    #--------------------------------------------------------------------------
    def __init__(self, json_data=None, prefix=None):
        self.options = []
        if json_data is not None:
            normalize = lambda p: _normalize_path(p, prefix)
            self.options = _normalize_values(json_data, normalize)

    #--------------------------------------------------------------------------
    def __repr__(self):
        return repr(self.options)

    #--------------------------------------------------------------------------
    def __getitem__(self, language):
        if language is None:
            if type(self.options) is not dict:
                return self.options

            # TODO compute union of flags

        if type(self.options) is dict:
            return _get(language, self.options, [])

        return self.options

#==============================================================================
class Configuration(Object):
    #--------------------------------------------------------------------------
    def __init__(self, json_data, prefix=None, package=None, parent=None):
        self.compile_features = []
        self.compile_flags = LanguageOptions()
        self.definitions = LanguageOptions()
        self.includes = LanguageOptions()
        self.link_features = []
        self.link_flags = LanguageOptions()
        self.link_languages = ['c']
        self.link_libraries = []
        self.location = None
        self.link_location = None
        self.requires = []
        self.link_requires = []

        super(Configuration, self).__init__(json_data)

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

        get_or_inherit('compile-features', _get_normalized, _normalize_feature)
        get_or_inherit('compile-flags', make_language_options)
        get_or_inherit('definitions', make_language_options)
        get_or_inherit('includes', make_language_options, prefix)
        get_or_inherit('link-features', _get_normalized, _normalize_feature)
        get_or_inherit('link-flags', make_language_options)
        get_or_inherit('link-languages', _geti)
        get_or_inherit('link-libraries', _get)
        get_or_inherit('location', _get_canonical, prefix)
        get_or_inherit('link-location', _get_canonical, prefix)
        get_or_inherit('requires', _get, [])
        get_or_inherit('link-requires', _get, [])

        if package is not None:
            for i in range(len(self.requires)):
                if self.requires[i].startswith(':'):
                    self.requires[i] = package + self.requires[i]

        if self.link_location is None:
            self.link_location = self.location

#==============================================================================
class Component(Configuration):
    #--------------------------------------------------------------------------
    def __init__(self, json_data, prefix=None, package=None):
        super(Component, self).__init__(json_data, prefix, package)

        self.kind = _get('type', json_data, required=True)
        self.configurations = _make_dict(Configuration, 'configurations',
                                         json_data, prefix, package, self)

#==============================================================================
class Requirement(Object):
    #--------------------------------------------------------------------------
    def __init__(self, json_data):
        super(Requirement, self).__init__(json_data)

        self.hints = _get('hints', json_data, [])
        self.components = _get('components', json_data, [])
        self.version = _get('version', json_data)

#==============================================================================
class Platform(Object):
    #==========================================================================
    class Runtime(object):
        def __init__(self, language, json_data):
            self.vendor = _geti('%s-vendor' % language, json_data)
            self.version = _get('%s-version' % language, json_data)

        def __repr__(self):
            return repr(self.__dict__)

    #--------------------------------------------------------------------------
    def __init__(self, json_data):
        super(Platform, self).__init__(json_data)

        self.isa = _geti('isa', json_data)
        self.kernel = _geti('kernel', json_data)
        self.c_runtime = Platform.Runtime('c-runtime', json_data)
        self.cpp_runtime = Platform.Runtime('cpp-runtime', json_data)
        self.clr = Platform.Runtime('clr', json_data)
        self.jvm = Platform.Runtime('jvm', json_data)

#==============================================================================
class Package(Object):
    #--------------------------------------------------------------------------
    def __init__(self, path, json_data):
        super(Package, self).__init__(json_data)

        cps_version = _make(sv.Version, 'cps-version', json_data)
        if cps_version not in supported_cps_versions:
            raise NotImplementedError('CPS version %s is not supported' %
                                      cps_version)

        self.name = _get('name', json_data, required=True)
        self.platform = _make(Platform, 'platform', json_data)
        self.version = _get('version', json_data)
        self.compat_version = _get('compat-version', json_data)
        self.configurations = _get('configurations', json_data, [])
        self.default_components = _get('default-components', json_data, [])

        if path is not None:
            cps_path = _get('cps-path', json_data, '')
            prefix = '@prefix@' # FIXME
        else:
            prefix = None

        self.requires = _make_dict(Requirement, 'requires', json_data)
        self.components = _make_dict(Component, 'components', json_data,
                                     prefix, self.name)

        if self.compat_version is None:
            self.compat_version = self.version

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#------------------------------------------------------------------------------
def _dvmap(func, d):
    return {key: func(value) for key, value in iteritems(d)}

#------------------------------------------------------------------------------
def _normalize_path(path, prefix):
    if path is not None and prefix is not None:
        if path.startswith('@prefix@'):
            return prefix + path[8:]

    return path

#------------------------------------------------------------------------------
def _normalize_feature(feature):
    if feature is None:
        return None

    if feature.lower() in {'warn:error', 'nowarn:error'}:
        return feature.lower()

    feature_parts = feature.split(':')
    feature_parts[0] = feature_parts[0].lower()
    return ':'.join(feature_parts)

#------------------------------------------------------------------------------
def _normalize_values(json_data, normalize_function):
    normalize_recurse = lambda v: _normalize_values(v, normalize_function)

    if type(json_data) is dict:
        return _dvmap(normalize_recurse, json_data)

    elif type(json_data) is list:
        return map(normalize_recurse, json_data)

    elif type(json_data) is unicode:
        return normalize_function(json_data)

    else:
        return json_data

#------------------------------------------------------------------------------
def _get(key, json_data, default=None, required=False):
    key = key.lower()
    for jk, jv in iteritems(json_data):
        if jk.lower() == key:
            return jv if jv is not None else default

    if required:
        raise KeyError(key)

    return default

#------------------------------------------------------------------------------
def _get_normalized(key, json_data, normalize_function, default=None):
    return _normalize_values(_get(key, json_data, default), normalize_function)

#------------------------------------------------------------------------------
def _geti(key, json_data, default=None):
    return _get_normalized(key, json_data, lambda s: s.lower(), default)

#------------------------------------------------------------------------------
def _get_canonical(key, json_data, prefix, default=None):
    return _normalize_path(_get(key, json_data, default), prefix)

#------------------------------------------------------------------------------
def _make(constructor, key, json_data, *args):
    json_data = _get(key, json_data)
    if json_data is not None:
        return constructor(json_data, *args)

    return None

#------------------------------------------------------------------------------
def _make_dict(constructor, key, json_data, *args):
    result = {}
    for name, data in iteritems(_get(key, json_data, {})):
        result[name] = constructor(data, *args)

    return result

#------------------------------------------------------------------------------
def get_extension(obj, name, default=None):
    return _get(name, obj.extensions, default)

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

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

if __name__ == '__main__':
    import sys
    print(read(sys.argv[1]))
