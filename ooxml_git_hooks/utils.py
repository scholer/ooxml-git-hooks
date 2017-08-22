

import sys
import os
import re
import pathlib
import fnmatch
import glob
import zipfile
import hashlib


IGNORE = [
    '.unzipped/'
]


DIRECTORIES = [
    # ooxml pattern: {configuraton} - or just a list of {configuration}s ?
    # Maybe say if we have ooxml is a key pattern, e.g. '.docx' then convert to '**/*.docx' glob-style pattern?

]

# formatting variables (example: ./path/to/file.docx
# * filepath    ./path/to/file.docx
# * filename    file.docx
# * fnbase      file    # or `stem`, which is what the pathlib module uses?
# * fpnoext     ./path/to/file
# * fnext       .docx   # or `suffix`, which is what the pathlib module uses?
# * filetype    docx
# * dirpath     ./path/to


DEFAULT_CONVERSION = {
    'include': ('**/*.docx', '**/*.pptx', '**/*.xlsx'),
    'ignore': '.ooxml_store/*',
    'pandoc_fnfmt': '{fpnoext}.md',
    'untip_dirfmt': '.ooxml_store/{filepath}/',
    # Create regex from 'unzip_dir' pattern. Or just have the original filename in a metadata file.
    'rezip_regex': None,
}


def find_files(rootdir, glob_pats, excludes=None, unix_globbing=True, exclude_match_dirs=True):
    # OBS: Unlike Unix glob, Python's glob/fnmatch modules does NOT treat '/' as a special character.
    # That is, '*' will match '/' characters.
    # Unix:   ``fnmatch('path/to/file.txt', '*.txt') -> False``
    # Unix:   ``fnmatch('path/to/file.txt', '**/*.txt') -> True``
    # Python: ``fnmatch('path/to/file.txt', '*.txt') -> True``
    # Python's fnmatch just translates the glob pattern to regex, compiles, and returns the match function.
    #   '*' in the glob pattern is converted to '.*'. You could just change that to '[^//]*'.
    # So, roll your own fnmatch->regex translator if you need posix-like matching:
    # Edit: Starting with Python 3.5, glob now supports unix-like recursive globbing with '**'.
    # For earlier versions of Python, use e.g. glob2 or formic packages.
    if isinstance(glob_pats, str):
        glob_pats = [glob_pats]
    if isinstance(excludes, str):
        excludes = [excludes]

    result = []
    result_set = set()

    def not_excluded(fp):
        if excludes:
            return not any(fnmatch.fnmatch(fp, pat) for pat in excludes)
        else:
            return True

    def not_in_result_set(fp):
        return fp not in result_set

    if unix_globbing:
        # '*.png' will only match 'file.png' but not 'path/to/file.png'
        # Use '**/*.png' to match png files in all sub-directories.
        # Use '*/*/*.png' to match png files exactly two levels deep.
        # This is Git's default globbing style.
        for pattern in glob_pats:
            matches = glob.glob(pattern, recursive=True)
            files = filter(os.path.isfile, matches)
            files = filter(not_excluded, files)
            files = filter(not_in_result_set, files)
            files = list(files)
            result.extend(files)
            result_set.update(set(files))
    else:
        # '*.png' will match 'file.png' and '/path/to/file.png'
        for root, dirs, files in os.walk(rootdir):
            for fn in files:
                fpath = os.path.join(root, fn)
                if excludes and any(fnmatch.fnmatch(fpath, pat) for pat in excludes):
                    continue
                if any(fnmatch.fnmatch(fpath, pat) for pat in glob_pats):
                    result.append(fpath)
            # Excluded dirs:
            # We must update `dirs` in-place, which is a bit awkward:
            if exclude_match_dirs and excludes:
                exclude_dirs = [
                    dirname for dirname in dirs
                    if any(fnmatch.fnmatch(fpath, pat) for pat in excludes)
                ]
                # Removing in reversed order should perform slightly better:
                for dirname in reversed(exclude_dirs):
                    dirs.remove(dirname)

    return result


def regex_from_pathfmt(pathfmt, fnchars="[^//]", do_test=True):
    """Convert a path-format str to regex pattern."""
    fmtpat = r"\{\w+\}"
    matches = re.findall(fmtpat, pathfmt)
    path_regex = pathfmt
    for varname in matches:
        regex = r"(?P<%s>%s+)" % (varname, fnchars)
        # replace "{varname}" with "(?P<varname>[^//]+)"
        path_regex = re.sub("{%s}" % (varname,), regex, path_regex)
    if do_test:
        test_path_regex(path_regex=path_regex, pathfmt=pathfmt)
    return path_regex


def test_path_regex(path_regex, pathfmt, testset=None):
    """Assert that path_regex properly captures the variables of pathfmt."""
    if testset is None:
        testset = [
            dict(inputfn='path/to/file.docx', glob_pat='**/*.docx'),
        ]
    for params in testset:
        inputfn, glob_pat = params['inputfn'], params['glob_pat']
        pathobj = pathlib.Path(inputfn)
        assert pathobj.match(glob_pat)
        filename_attrs = get_filename_attrs(inputfn)
        outputdir = pathfmt.format(**filename_attrs)
        match = re.match(path_regex, outputdir)
        # Make sure we can re-create filepath from match groups!


def recreate_filepath(matchdict):
    if 'filepath' in matchdict:
        return matchdict['filepath']
    if 'dirpath' in matchdict:
        dirpath = matchdict['dirpath']
        if 'filename' in matchdict:
            return os.path.join(dirpath, matchdict['filename'])
        elif 'stem' in matchdict:
            if 'suffix' in matchdict:
                return os.path.join(dirpath, matchdict['stem']+matchdict['suffix'])
            elif 'filetype' in matchdict:
                return os.path.join(dirpath, matchdict['stem']+'.'+matchdict['filetype'])
    raise ValueError("Could not recreate filepath from matchdict %s" % (matchdict,))


def get_filename_attrs(filepath):
    # See https://www.python.org/dev/peps/pep-0428/
    # For a discussion of "suffix" vs "ext" and "base" vs "stem", see:
    #  * https://groups.google.com/forum/#!topic/python-ideas/f4fZfY1HLJs%5B1-25%5D
    #  * https://groups.google.com/d/msg/python-ideas/f4fZfY1HLJs/2FSCObPdTKEJ
    #

    p = pathlib.Path(filepath)
    return dict(
        filepath=filepath, path=filepath,
        dirpath=p.parent, parent=p.parent,
        filename=p.name, name=p.name,
        stem=p.stem,
        suffix=p.suffix,
        filetype=p.suffix.strip('.') if p.suffix else None,
    )


def as_posix_path_str(path):
    """Ensure that a filepath str that has forward slashes regardless of platform."""
    return pathlib.PurePath(path).as_posix()

pp = as_posix_path_str  # alias


# From pptx-downsizer package:
def zip_directory(
        directory, targetfn=None, relative=True,
        overwrite=None,
        compress_type=zipfile.ZIP_DEFLATED, verbose=1
):
    """Zip all files and folders in a directory.

    Args:
        directory: The directory whose contents should be zipped.
        targetfn: Output filename of the zipped archive.
        relative: If True, make the arcname relative to the input directory.
        compress_type: Which kind of compression to use. See zipfile package.
        verbose: How much information to print to stdout while creating the archive.

    Returns:
        The filename of the zipped archive.

    """
    assert os.path.isdir(directory)
    if targetfn is None:
        targetfn = directory + ".zip"
    filecount = 0
    if verbose and verbose > 0:
        print("Creating archive %r from directory %r:" % (targetfn, directory))

    if os.path.exists(targetfn):
        if overwrite is None:
            print("""
NOTICE: Output file %r already exists.
If you want to keep the old file, please move/rename it before continuing.""" % (targetfn,))
            input("Press enter to continue... ")
        elif overwrite is False:
            raise FileExistsError("Target file %r already exists and overwrite set to %r" % (targetfn, overwrite))

    with zipfile.ZipFile(targetfn, mode="w") as zipfd:
        for dirpath, dirnames, filenames in os.walk(directory):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                arcname = os.path.relpath(fpath, start=directory) if relative else fpath
                if verbose and verbose > 0:
                    print(" - adding %r" % (arcname,))
                zipfd.write(fpath, arcname=arcname, compress_type=compress_type)
                filecount += 1
    if verbose and verbose > 0:
        print("\n%s files written to archive %r" % (filecount, targetfn))
    return targetfn


def hash_file(filepath, method='md5', filemode='rb', single_read=None, blocksize=64*1024, digest='hexdigest'):
    """

    Args:
        filepath:
        method:
        filemode:
        single_read:
        blocksize:
        digest:

    Returns:

    Refs:
    * https://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
    * https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    * http://pythoncentral.io/hashing-files-with-python/
    """
    if isinstance(method, str):
        method = getattr(hashlib, method)
    hasher = method()
    if single_read is None:
        # If file is small, just read the whole file in a single read:
        single_read = os.path.getsize(filepath) < 2**20
    with open(filepath, mode=filemode) as fd:
        if single_read:
            hasher.update(fd.read())
        else:
            for b in iter(lambda: fd.read(blocksize), b''):
                hasher.update(b)
    if not digest:
        return hasher
    elif isinstance(digest, str):
        return getattr(hasher, digest)()  # e.g. hasher.hexdigest()
    else:
        return digest(hasher)


def prettyprint_xml(text, method='stdlib-xml', indent=" "*4):
    """

    Args:
        text:
        method:

    Returns:
        pretty, indented xml str

    Alternatives:

    * xmllint command line tool (from libxml2-utils)
    * xml_pp - from XML::Twig perl module.
    * xmlstarlet -
    * tidy -
    * saxon-lint
    *
    * xmlpp - http://xmlpp.codeplex.com/
    * pyxml
    * xmlformatter - command line tool - https://github.com/pamoller/xmlformatter
    * XMLLayout (2011)



    Refs:
    * https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    * https://stackoverflow.com/questions/16090869/how-to-pretty-print-xml-from-the-command-line
    * https://stackoverflow.com/questions/3844360/best-way-to-generate-xml

    """

    if method is None:
        method = 'stdlib-xml'
    if indent is None:
        indent = " "*4

    if method == 'lxml':
        # https://stackoverflow.com/a/3844432/3241277
        import lxml
        pretty = lxml.etree.tostring(lxml.etree.fromstring(text), pretty_print=True)
    elif method == 'vkbeautify':
        # https://stackoverflow.com/a/41455013/3241277
        import vkbeautify
        pretty = vkbeautify.xml(text)
    elif method in ('beautifulsoup', 'bs'):
        # https://stackoverflow.com/a/39482716/3241277
        import bs4
        bs = bs4.BeautifulSoup(text, 'xml')
        pretty = bs.prettify()
    elif method == 'yattag':
        # https://stackoverflow.com/a/23634596/3241277
        import yattag
        pretty = yattag.indent(text)
    else:  # if method == 'stdlib-xml':
        # https://stackoverflow.com/a/749839/3241277
        import xml.dom.minidom
        print("Converting text", type(text))
        print("indent: %r" % indent)
        tree = xml.dom.minidom.parseString(text)
        pretty = tree.toprettyxml(indent=indent)

    return pretty


