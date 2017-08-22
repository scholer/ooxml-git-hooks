


import sys
import click

from .utils import prettyprint_xml


@click.command()
@click.argument('files', nargs=-1)
@click.option('--outputfn')
@click.option('--method')
@click.option('--indent', default=" "*4)
def prettify_xml_cli(files, outputfn=None, method=None, indent=" "*4):
    if not files:
        files = ("-",)
    print("Files:", files)
    for inputfn in files:
        if inputfn is None or inputfn == "-":
            text = sys.stdin.read()
        else:
            text = open(inputfn).read()

        pretty = prettyprint_xml(text, method=method, indent=indent)
        if outputfn is None:
            print(pretty)
        elif outputfn == '-':
            return pretty
        else:
            with open(outputfn, 'w') as fd:
                fd.write(pretty)
