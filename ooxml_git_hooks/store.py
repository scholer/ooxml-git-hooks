
"""

Regarding not getting .gitignored:
* Make sure stores does not end with an excluded filetype, e.g. by adding a suffix: `file.docx.store`.
* Use the exclude directive in the .gitignore:
    !*.docx/*


Usage, ooxml-store=ooxml_git_hooks.store:cli entry point:

    # Store files to .ooxml_store/ directory:
    ooxml-store store-file <file>
    ooxml-store store-all

    # Recreate files stored in .ooxml_store/ directory:
    ooxml-store recreate-file <file>
    ooxml-store recreate-all


"""

# TODO: Opening .docx files with zipfile.ZipFile() sometimes fails if file is open in Word. Copy file before unzipping!

import os
import zipfile
import shutil
import yaml
import pypandoc
import click

from ooxml_git_hooks.utils import get_filename_attrs, zip_directory, find_files, hash_file


# TODO: Read these from config file:
FILE_METADATA_FN = "ooxml_metadata.yaml"
STORE_ROOT = '.ooxml_store'
IGNORE = ('.ooxml_store/*', "**/~$*")
INCLUDE = ('**/*.docx', '**/*.pptx', '**/*.xlsx')
# OBS: Using just the filepath can cause directories to be .gitignored.
# Add `!.ooxml_store/**` to .gitignore to make sure the ooxml_store files are included.
STORE_DIRFMT = '{filepath}.store/'
# STORE_DIRFMT = '{filepath}/'
PANDOC_FNFMT = '{fpnoext}.md'
INDEX_FN = 'index.yaml'
HASH_METHOD = 'md5'
DEFAULT_METADATA = {
    'archive': '.zip',
}


@click.group()
def cli():
    pass


@click.command(name="store-all")
def store_all_cli(basedir=".", **kwargs):
    store_all(basedir, **kwargs)


def store_all(
        basedir=".",
        include=INCLUDE,
        ignore=IGNORE,
        store_root=STORE_ROOT,
        store_dirfmt=STORE_DIRFMT,
        pandoc_fnfmt=PANDOC_FNFMT,
        # configfn=None,
        clean=True,
        verbose=2,
):
    """"""
    # TODO: Option to only process changed files.
    # For instance,
    # Q: How does git determine which files have changed? A: It records `lstat` information.

    if verbose and verbose > 1:
        print("\nCreating store...")

    if clean:
        if verbose and verbose > 1:
            print(" - Removing old store...")
        # os.removedirs(store_root)
        shutil.rmtree(store_root)
        os.mkdir(store_root)

    # print(f"finding files: rootdir={basedir!r}, glob_pats={include!r}, excludes={ignore!r}")
    input_files = find_files(rootdir=basedir, glob_pats=include, excludes=ignore)
    if verbose and verbose > 1:
        print(" - Adding files to store:", input_files)

    for filepath in input_files:
        if os.path.basename(filepath).startswith("~$"):
            print("SKIPPING FILE: %r" % (filepath,))
            continue
        store_file(filepath, store_root=store_root, store_dirfmt=store_dirfmt)


@click.command(name="store-file")
@click.argument('filename', type=click.Path(exists=True))
def store_file_cli(
        filename,
        store_root=STORE_ROOT, store_dirfmt=STORE_DIRFMT,
        pandoc_fnfmt=None,
        verbose=2
):
    store_file(filename, store_root=store_root, store_dirfmt=store_dirfmt, pandoc_fnfmt=pandoc_fnfmt, verbose=verbose)


def store_file(
        filename,
        store_root=STORE_ROOT, store_dirfmt=STORE_DIRFMT,
        pandoc_fnfmt="{store_dir}/{stem}.md",
        add_lstat=True, add_hash='md5',
        verbose=2
):

    inputfn_attrs = get_filename_attrs(filename)

    store_dir = os.path.join(store_root, store_dirfmt).format(store_root=store_root, **inputfn_attrs)

    if verbose and verbose > 0:
        print("Creating store %r for file %r" % (store_dir, filename))

    config = DEFAULT_METADATA.copy()
    archive_dir = os.path.join(store_dir, config['archive'])
    os.makedirs(archive_dir)
    config['inputfn'] = filename

    if add_hash:
        if add_hash is True:
            add_hash = HASH_METHOD
        config['hash_method'] = add_hash
        config['hash_hexdigest'] = hash_file(filename)

    if add_lstat:
        # (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)
        # Do not include atime, it is frequently updated (e.g. by search indexing).
        lstat = os.lstat(filename)
        stat_attrs = (
            'st_size',  # size, in bytes
            'st_ctime', 'st_ctime_ns',  # time of creation (Windows) or change (Unix)
            'st_mtime', 'st_mtime_ns',  # time of modificaton.
            'st_nlink', 'st_dev', 'st_ino',  # device, inode
            'st_mode', 'st_uid', 'st_gid',  # filemode, user id, group id,
            # 'st_flags', 'st_gen',  # user-defined flags, generation,
        )
        config['lstat'] = {a: getattr(lstat, a, 0) for a in stat_attrs}  # list(lstat)

    try:
        with zipfile.ZipFile(filename, 'r') as zipfd:
            zipfd.extractall(archive_dir)
    except zipfile.BadZipfile:
        import tempfile
        with tempfile.TemporaryDirectory() as tempdir:
            tempfn = os.path.join(tempdir, inputfn_attrs['name'])
            print("Copying %r -> %r" % (filename, tempfn))
            shutil.copyfile(filename, tempfn)
            with zipfile.ZipFile(tempfn, 'r') as zipfd:
                zipfd.extractall(archive_dir)

    if pandoc_fnfmt:
        pandoc_supported_formats = pypandoc.get_pandoc_formats()  # from, to
        if isinstance(pandoc_fnfmt, str):
            pandoc_fnfmt = [pandoc_fnfmt]
        for output_fnfmt in pandoc_fnfmt:
            pandoc_fn = output_fnfmt.format(store_root=store_root, store_dir=store_dir, **inputfn_attrs)
            assert '.' in pandoc_fn
            output_format = pandoc_fn.rsplit('.')[-1]
            # if output_format not in pandoc_supported_formats[0]:
            #     print(" - Output format %r not supported by Pandoc!" % output_format)
            # elif inputfn_attrs['filetype'] not in pandoc_supported_formats[1]:
            #     print(" - Input  format %r not supported by Pandoc!" % inputfn_attrs['filetype'])
            # else:
            try:
                if verbose and verbose > 1:
                    print(" - Making %s file: %r -> %r" % (output_format, filename, pandoc_fn))
                pypandoc.convert_file(filename, output_format, outputfile=pandoc_fn)
            except RuntimeError as exc:
                print(" - Could not convert with pandoc: %s" % (exc,))
    metadata_fn = os.path.join(store_dir, FILE_METADATA_FN)

    with open(metadata_fn, 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


@click.command(name="recreate-file")
@click.argument('store_dir', type=click.Path(exists=True))
def recreate_file_cli(store_dir, target_fn=None, overwrite=None, verbose=2):
    recreate_stored_file(store_dir, target_fn=target_fn, overwrite=overwrite, verbose=verbose)


def recreate_stored_file(
        store_dir, target_fn=None, overwrite=None,
        skip_if_unchanged=False, skip_test="lstat",
        verbose=2
):
    """"""

    if verbose:
        print("\nRe-creating ooxml file from store directory %r" % (store_dir,))
    metadata_fn = os.path.join(store_dir, FILE_METADATA_FN)
    if verbose and verbose > 1:
        print("\n - Reading metadata:", metadata_fn)
    config = yaml.load(open(metadata_fn))

    if target_fn is None:
        target_fn = config['inputfn']

    if os.path.exists(target_fn):
        assert os.path.isfile(target_fn)
        if 'lstat' in config:
            lstat = config['lstat']


    archive_dir = os.path.join(store_dir, config['archive'])

    if verbose and verbose > 1:
        print(" - Creating ooxml/zipfile %r from store archive %r..." % (target_fn, archive_dir))
    zip_directory(directory=archive_dir, overwrite=overwrite, targetfn=target_fn)


@click.command(name="recreate-all")
@click.option('--overwrite', is_flag=True, default=None)
@click.option('--use-index', is_flag=True, default=None)
def recreate_all_cli(store_root=STORE_ROOT, use_index=None, overwrite=None, verbose=2):
    recreate_all(store_root=store_root, use_index=use_index, overwrite=overwrite, verbose=verbose)


def recreate_all(
        store_root=STORE_ROOT, use_index=None, overwrite=None, verbose=2
):
    """"""
    # TODO: Only re-create changed files.

    if verbose and verbose > 0:
        print("\nRe-creating all files in store_root %r" % (store_root,))
    index_fn = os.path.join(store_root, INDEX_FN)
    if use_index is None:
        use_index = os.path.isfile(index_fn)

    if use_index:
        if verbose and verbose > 0:
            print(" - Reading index: %r" % (index_fn,))
        index = yaml.load(open(index_fn))
        if isinstance(index, dict):
            # inputfn: store_dir,  but we only need the store_dir
            store_dirs = index.values()
        else:
            # just a list of store_dirs
            store_dirs = index
    else:
        glob_pat = os.path.join(store_root, "**", FILE_METADATA_FN)
        print("Metadata glob_pat:", glob_pat)
        metadata_files = find_files(
            rootdir=store_root, glob_pats=glob_pat, unix_globbing=True)
        if verbose and verbose > 0:
            print(" - %s store metadata files located" % (len(metadata_files),))
        store_dirs = [os.path.dirname(metadata_fn) for metadata_fn in metadata_files]
        assert all(os.path.isdir(d) for d in store_dirs)

    for store_dir in store_dirs:
        recreate_stored_file(store_dir, overwrite=overwrite)

# Add click commands to the click `cli` group:
cli.add_command(store_all_cli, name="store-all")
cli.add_command(store_file_cli, name="store-file")
cli.add_command(recreate_file_cli, name="recreate-file")
# cli.add_command(recreate_stored_file)
cli.add_command(recreate_all_cli, name="recreate-all")


