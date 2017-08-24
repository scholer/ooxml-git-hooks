try:
    # Uset setuptools if available to prevent "UserWarning: Unknown distribution option: 'entry_points'"
    from setuptools import setup
except ImportError:
    from distutils.core import setup

"""

ooxml-git-hooks:
================

Python environments::
    
``ooxml-git-dev``:
    Has main git repo installed in "editable" mode with ``pip install -e .``
    ``conda create -n ooxml-git-dev python pip pillow pyyaml docutils pandoc`` 

``ooxml-git-build-test``:
    For installing and testing the ``dist/ooxml-git-hooks-<verson>.tar.gz`` builds.
    ``source activate ooxml-git-build-test``

``ooxml-git-pypi-test``:
    For testing the package uploaded to PyPI.
    

Release protocol:

0. Open a new terminal tab for each of the three environments above.

1. Make sure all tests passes in the dev environment ``ooxml-git-hooks-dev``.
   Verify that all entry points are functional and able to successfully complete.
   Preferably verify that it works both when invoked from console and from Automator scripts (particularly: stdout).
   Check that README.rst is correctly formatted::

   ``python setup.py check --restructuredtext``  (``docutils`` must be installed)

2. Bump version number:
   ``version``+``download_url`` in ``setup.py`` 
   and ``version`` in ``ooxml_git/__init__.py``),
   then ``git commit`` (or maybe do that after uploading release).

3. Build release:
    (a) Change to dedicated build/dist environment, e.g. ``ooxml-git-hooks-build-test``.
    (b) Clear the old version: ``pip uninstall ooxml-git-hooks`` (or do a complete wipe).
    (c) Go to project root directory in terminal and build release with ``python setup.py sdist``,
    (d) Install build in sdist environment using ``pip install dist/ooxml-git-hooks-<version>.tar.gz``,
    (e) Run tests and verify that all entry points are working.

4. Register upload release and source distribution to PyPI TEST site:
   ``python setup.py sdist upload -r pypitest_legacy``,
   then check https://testpypi.python.org/pypi/ooxml-git-hooks/ and make sure it looks right.
   Note: Previously, this was a two-step process, requiring pre-registration with 
   ``python setup.py register -r pypi(test)``. This is no longer needed.  

5. Register and upload release to production PyPI site and check https://pypi.python.org/pypi/ooxml-git-hooks/
   ``python setup.py sdist upload -r pypi``.

6. Test the PYPI release using the ``ooxml-git-hooks-pypi-test`` environment,
   preferably also on a different platforms as well (Windows/Mac/Linux).
   Use ``pip install -U ooxml-git-hooks`` to update, or do a complete 
   wipe+reinstall of the ``ooxml-git-hooks-pypi-test`` environment.

7. Commit, tag, and push:
   Add all updated files to git (``git status``, then ``git add -u``), 
   and commit (``git commit -m "message"``).
   Tag and annotate this version in git with ``git tag -a <version> -m "message"``,
   then push it with ``git push --follow-tags`` 
   (or ``git push --tags`` if you have already pushed the branch/commits).
   Check that everything looks good on the GitHub page, https://github.com/scholer/ooxml-git-hooks
   You can also create tags/releases using GitHub's interface, c.f. 
   https://help.github.com/articles/creating-releases/.

8. Update ``version`` again, adding "-dev" postfix.

If you find an error at any point, go back to step 1.



Regarding PyPI and packaging/distribution:
* You can use a .pypirc to configure server/username/password (can be configured globally in ~/.pypirc).
* https://wiki.python.org/moin/TestPyPI
* https://wiki.python.org/moin/CheeseShopTutorial
* https://packaging.python.org/tutorials/distributing-packages/
* https://mail.python.org/pipermail/distutils-sig/2017-June/030766.html
* http://inre.dundeemt.com/2014-05-04/pypi-vs-readme-rst-a-tale-of-frustration-and-unnecessary-binding/  (OLD)
* http://python-packaging.readthedocs.io/en/latest/metadata.html
* https://docs.python.org/devguide/documenting.html

Regarding reStructuredText and Markdown:
* http://docutils.sourceforge.net/rst.html
* Markdown to rST using Pandoc: ``pandoc --from=markdown --to=rst --output=README.rst README.md``
* Fix line wrap using pandoc: ``pandoc README.rst -o README.rst`` [may also change a lot of other stuff!]
* Using docutils: ``python setup.py check --restructuredtext``
* Linting using restructuredtext_lint: ``rst-lint README.rst``
* https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet
* https://en.support.wordpress.com/markdown-quick-reference/
* http://www.sphinx-doc.org/en/stable/rest.html
* http://docutils.sourceforge.net/docs/user/rst/quickstart.html
* http://docutils.sourceforge.net/rst.html
* https://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html


"""

# try:
#     import pypandoc
#     long_description = pypandoc.convert_file('README.md', 'rst')
#     long_description = long_description.replace("\r", "")
# except (ImportError, OSError):
#     print("NOTE: pypandoc not available, reading README.md as-is.")
# Edit, switched to using reStructuredText for README file:
try:
    long_description = open('README.rst').read()
except FileNotFoundError:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', to='rst')


# update 'version' and 'download_url', as well as pptx_downsizer.__init__.__version__
setup(
    name='ooxml-git-hooks',
    description='Tools for uncompressing Microsoft Office (Office Open XML) files for better git version control.',
    long_description=long_description,
    url='https://github.com/scholer/ooxml-git-hooks',
    packages=['ooxml_git_hooks'],  # List all packages (directories) to include in the source dist.
    version='0.1.1-dev',  # Update for each new version
    # download_url='https://github.com/scholer/ooxml-git-hooks/tarball/0.1.2',  # Update for each new version
    download_url='https://github.com/scholer/ooxml-git-hooks/archive/master.zip',
    author='Rasmus Scholer Sorensen',
    author_email='rasmusscholer@gmail.com',
    license='GNU General Public License v3 (GPLv3)',
    keywords=[
        "ooxml",
        "Office Open",
        "git",
        "pptx",
        "docx",
        "xlsx",
        "Word",
        "Excel",
        "PowerPoint",
        "compression",
        "versioning",
        "version control",
    ],
    # Automatic script creation using entry points has largely super-seeded the "scripts" keyword.
    # you specify: name-of-executable-script: module[.submodule]:function
    # When the package is installed with pip, a script is automatically created (.exe for Windows).
    # Note: The entry points are stored in ./<package name>.egg-info/entry_points.txt, which is used by pkg_resources.
    entry_points={
        'console_scripts': [
            # These should all be lower-case, else you may get an error when uninstalling:
            'ooxml-store=ooxml_git_hooks.store:cli',
            'prettify-xml=ooxml_git_hooks.cli:prettify_xml_cli',

        ],
    },
    # install_requires: Minimal requirement for this project.
    # (Whereas `requirements.txt` is typically used to produce a comprehensive python environment.)
    install_requires=[
        'pyyaml',
        'click',
    ],
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        # 'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',

        # 'Topic :: Software Development :: Build Tools',
        'Topic :: Education',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Office Suites',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',

        'Environment :: Console',

        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX :: Linux',
    ],

)
