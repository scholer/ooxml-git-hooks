ooxml-git-hooks
===============

Pre-commit and post-checkout hooks and tools making git better suited for version control
of zipped Office Open XML files, e.g. Word/.docx, Excel/.xlsx, and PowerPoint/.pptx files.



Basic usage:
------------

Usage of the ``ooxml-store=ooxml_git_hooks.store:cli`` entry point::

    # Store files to .ooxml_store/ directory:
    ooxml-store store-file <file>
    ooxml-store store-all

    # Recreate files stored in .ooxml_store/ directory:
    ooxml-store recreate-file <file>
    ooxml-store recreate-all



Installation:
-------------

Installation with pip::

    pip install ooxml-git-hooks



Setting up Git:
---------------


Alter repository config, ``.git/config``::

    # Add git hooks (optional):

    # Better xml diffs:
    [diff "xml"]
    textconv = prettify-xml


Modify worktree ``.gitattributes`` or repository ``$GIT_DIR/info/attributes`` file::

    # *.pptx diff=zip
    *.xml diff=xml
    *.rels diff=xml


Finally, make sure your git repository is not located inside your Dropbox
(or other sync service), as that can corrupt your git repository.
It is still possible to have the files you are working on inside Dropbox,
you just have to keep your "working directory" and the git repository separate.
See the "Separating repository and working directory" section at the bottom
of this readme for more information.



Development notes:
==================

**Project name?**

Keywords: ooxml, zip, git, gitter, hooks, storage, store, manager, stage, staging,
push, pusher, booker, revision, version, versioning, library, librarian.

Suggestions:

* ooxml-git-hooks
* ooxml-git
* ooxml-git-store
* ooxml-git-storage
* ooxml-git-pusher
* ooxml-for-git
* ooxml-gitter
* ooxml-store-manager
* ooxml-stage-manager
* ooxml-hooka
* ooxml-git-stager
* ooxml-accountant
* ooxml-librarian
*


Package name?

* ooxml_store?
* ooxml_git_hooks?


Git hook vs manual command?

* Hook is convenient, especially if the repository is only used for versioning ooxml files.
* However, git hooks may be surprising, so could also just use the entry points manually.


Nomenclature:

* ``ooxml-store``, with hyphen, is used to denote the project name and the main entry point / "executable".
* ``ooxml_store``, with underscore, is used to denote the package name,
  and is also used for the storage directory, ``.ooxml_store``.


Features:

* Extract ooxml and other zip files.
* Create markdown mirror files.


Options:

* Which files to process (match by filename pattern, e.g. ``*.docx``).
* Where and how to extract the zip files.
* Whether to create pandoc mirrors e.g. in Markdown format.
* Whether to create md5 checksums of files.
* Have a '.ooxml_store' directory where all files are extracted (seems like a good idea).

Implementation:

* For each ooxml file, we have a directory:
* The directory should probably be placed so that it mirrors the location of the ooxml filepath.
* Alternatively, we could just have a random foldername (like a hash index), git can figure out how files have moved.
* In the directory we have::

    zip/
    md5checksums.txt - checksums of the extracted files, with the original ooxml file on top.
    metadata.yaml - metadata,

* In the root of the ooxml_store, we should probably have an index file that keeps track of the ooxml files stored here.
* Sure, we could just loop through all folders until we find folders that match a particular pattern,
    but that does seem inefficient.


TODO:

* We are currently purging the ``.ooxml_store`` directory every time we run ``ooxml-store store-all``.
  This is pretty fool proof: The store reflects exactly the ooxml files present in the working directory.
  (and selected by the file-glob filter). However, it is also obviously inefficient, especially if we have many
  ooxml files in the working directory and only one of them has been updated since last commit.
  So, consider using file-attributes to determine if files have been changed before purging.



Stackoverflow questions:

* https://stackoverflow.com/questions/17083502/how-to-perform-better-document-version-control-on-excel-files-and-sql-schema-fil
* https://stackoverflow.com/questions/8001663/can-git-treat-zip-files-as-directories-and-files-inside-the-zip-as-blobs

  * 15 votes for "no solutions currently, but a git-hook based setup should work" answer.
  *  9 votes for Sippey/Zippey git file filter solution - converting the zip file to a single large text-like file.
  *  6 votes for diff-only solution using ``textconv = unzip -c -a`` diff conversion.

* https://stackoverflow.com/questions/28357163/can-a-pre-commit-git-hook-zip-a-directory-and-add-it-to-the-repository
* https://stackoverflow.com/questions/17888604/git-with-large-files/19494211




References:
===========

Git references:

* https://git-scm.com/docs/githooks


Blogs posts, etc:
-----------------

Using Pandoc for version tracking/diffing of Word files:

* http://blog.martinfenner.org/2014/08/25/using-microsoft-word-with-git/
* https://github.com/vigente/gerardus/wiki/Integrate-git-diffs-with-word-docx-files
* https://ben.balter.com/2015/02/06/word-diff/ - See also github repo, /benbalter/word_diff
* http://tante.cc/2010/06/23/managing-zip-based-file-formats-in-git/
* https://paulhammant.com/2015/07/30/git-storing-unzipped-office-docs/

Managing zip-archives with Git:

* https://tante.cc/2010/06/23/managing-zip-based-file-formats-in-git/ - ``textconv = unzip -c -a`` when diffing .zip.


Mailing list posts:

* https://www.mail-archive.com/git@vger.kernel.org/msg68285.html


Prior art:

* https://xltools.net/excel-version-control/
* https://bitbucket.org/sippey/zippey - [Python] converts zipped files to unzipped "text-like" format (one file per zip-file).
* https://github.com/benbalter/word_diff - [Ruby] automatically converting any Word document committed to a GitHub repo to Markdown.
* https://github.com/ckrf/xlsx-git - [Shell] Convert .xlsx files to XML before committing them to git.


Other possibly-interesting projects:

* https://github.com/bup/bup - An incremental backup system for large files based on Git.
* https://git-lfs.github.com/ - Git Large File Storage (LFS), for versioning of large binary files.


Commit hook examples not related to zip files:

* https://github.com/drwahl/puppet-git-hooks
* https://github.com/pre-commit/pre-commit-hooks
* https://github.com/awslabs/git-secrets



Separating repository and working directory:
============================================

TL;DR: To combine Dropbox and Git, create a repository outside Dropbox, then
initialize the repository with the `--separate-git-dir <external-dir>` option::

    cd /Users/rasmus/Dropbox/path/to/your-folder-here
    git clone --separate-git-dir /Users/rasmus/Documents/git-repos/your-folder-here .

This will create a filesystem-agnostic Git symbolic link in your working directory,
linking to the external repository.


Background:
-----------

If your document is located inside dropbox, it may be beneficial to place
your repository outside the working directory in a location not managed by dropbox.
The reason is that dropbox can sometimes mess up git's repository, which would be
devastating to your repository. Adding insult to injury, the damages made by dropbox
to your git repository may not be immediately visible.
(Note: If you absolutely must have the repository inside Dropbox, use the git-bundle
format, where the whole repository is a single file, which is less likely to be corrupted
when dropbox syncs.)


In Git, a working directory must have exactly one git repository specified.
A git repository can have zero or one "main working tree", and zero or more "linked working trees".

You can execute git commands either from a working directory (usual case), or from a repository.

When inside a working tree, git must be able to locate the corresponding repository.
Git looks for the git repository (config) as follows:

1. If ``$GIT_DIR`` environment variable is set, use that.
2. If ``./.git`` is a text file with content being a directory path, use that directory.
3. Else, use ``./.git`` if it exists and is a directory.
4. Try 2 and 3 for all parent directories of the current folder.
5. If everything above fails to find a config, the git command fails.

When inside a repository, git determines the working tree as follows:

1. If ``--work-tree`` command line argument is given, use that.
2. If ``$GIT_WORK_TREE`` environment variable is given, use that.
3. Use the configured value of ``core.worktree``.
4. If ``core.worktree`` is not configured, commands operating on the current working directory
   are disabled (e.g. ``git status``).






