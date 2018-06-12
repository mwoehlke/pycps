CPS for Python
==============

This repository provides a Python module and some command-line tools for the `Common Package Specification`_. The module is intended to serve as a reference implementation for locating and parsing ``.cps`` files.

Requirements
------------

PyCPS requires:

- https://pypi.python.org/pypi/semantic_version/

Tools
-----

Currently, PyCPS contains two tools; ``cps2cmake`` and ``pc2cps``.

cps2cmake
'''''''''

``cps2cmake`` takes a CPS file and generates a CMake package configuration script. This is intended as an interim / legacy compatibility tool to allow users of older versions of CMake which do not have native CPS support to consume CPS packages in their CMake projects. Support is generally good, however not all features may be implemented. In particular, configuration-dependent attributes of components are not supported.

pc2cps
''''''

``pc2cps`` is a *very simple-minded* tool for converting pkg-config (``.pc``) files. Because pkg-config is a `highly impoverished <https://mwoehlke.github.io/cps/history.html#what-s-wrong-with-pkg-config>`_ format for describing a package, the resulting CPS is very crude. The input ``.pc`` file (a package name may be specified if the `pkgconf <https://github.com/pkgconf/pkgconf>`_ tool is available) is converted to a CPS having a single component, whose package name matches the input pkg-config file, and whose component name matches the ``Name`` attribute in the pkg-config file. The component is an ``"interface"`` component. There is basic support for ``"Includes"``, but no attempt is made to reverse engineer the link flags into the actual library location or type. There is, however, some support for CPS ``"Requires"`` which is populated from the pkg-config ``Requires`` attribute.

It is recommended that this tool be used only as an absolute last resort, as the resulting CPS's are of very low quality, do a poor job of correctly describing components, and rely on many CPS features that are intended only for legacy compatibility.

License
-------

PyCPS is distributed under the terms of the GNU Lesser General Public License, version 3 or later. The complete license may be found in the file LICENSE_ which is included in the project sources.

It is generally recognized that the outputs of a software tool are not derivative works of that tool unless they contain substantial and creative parts of the tool's code. The author(s) explicitly affirm that the outputs of the PyCPS tools are *not* derivative works of PyCPS, and are accordingly not subject to the terms of PyCPS's license. Such outputs may, however, be derivative works of files which PyCPS processes as inputs.

.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. _Common Package Specification: https://github.com/mwoehlke/cps/

.. _LICENSE: https://github.com/mwoehlke/pycps/blob/master/LICENSE
