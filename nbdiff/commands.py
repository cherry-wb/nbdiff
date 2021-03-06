'''
Entry points for the nbdiff package.
'''
from __future__ import print_function
import subprocess
import argparse
from .merge import notebook_merge
from .notebook_parser import NotebookParser
from .comparable import CellComparator
import json
import sys


def diff():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', nargs='*')
    args = parser.parse_args()
    # TODO take 0 or 2 arguments
    # if 0, use version control (unstaged changes)
    # if 2, use the files.
    length = len(args.notebook)
    if length == 2:
        x = NotebookParser()
        notebook1 = x.parse(open(args.notebook[0]))
        notebook2 = x.parse(open(args.notebook[1]))
        notequal = []
        for i in range(0, len(notebook1["worksheets"][0]["cells"])):
            cell1 = notebook1['worksheets'][0]['cells'][i]
            cell2 = notebook2['worksheets'][0]['cells'][i]
            if not CellComparator(cell1) == CellComparator(cell2):
                notequal.append((cell1, cell2))
        for cell1, cell2 in notequal:
            print(cell1)
            print(cell2)

    print('Arguments received: {}'.format(args.notebook))


def merge():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', nargs='*')
    args = parser.parse_args()
    length = len(args.notebook)
    parser = NotebookParser()

    if length == 0:
        # TODO error handling.
        # TODO handle more than one notebook file.
        # TODO ignore non-.ipynb files.
        output = subprocess.check_output("git ls-files --unmerged".split())
        output_array = [line.split() for line in output.splitlines()]

        if len(output_array) != 3:
            # TODO This should work for multiple conflicting notebooks.
            sys.stderr.write(
                "Can't find the conflicting notebook. Quitting.\n")
            sys.exit(-1)

        hash_array = []
        for line in output_array:
            hash = line[1]
            hash_array.append(hash)
        local_show = subprocess.Popen(
            ['git', 'show', hash_array[1]],
            stdout=subprocess.PIPE
        )
        nb_local = parser.parse(local_show.stdout)
        base_show = subprocess.Popen(
            ['git', 'show', hash_array[0]],
            stdout=subprocess.PIPE
        )
        nb_base = parser.parse(base_show.stdout)
        remote_show = subprocess.Popen(
            ['git', 'show', hash_array[2]],
            stdout=subprocess.PIPE
        )
        nb_remote = parser.parse(remote_show.stdout)
    elif length == 3 or length == 4:
        nb_local = parser.parse(open(args.notebook[0]))
        nb_base = parser.parse(open(args.notebook[1]))
        nb_remote = parser.parse(open(args.notebook[2]))
    else:
        sys.stderr.write('Incorrect number of arguments. Quitting.\n')
        sys.exit(-1)

    pre_merged_notebook = notebook_merge(nb_local, nb_base, nb_remote)
    if length == 3:
        # TODO ignore non-.ipynb files.

        # hg usage:
        # $ hg merge -t nbmerge <branch>

        # Mercurial gives three arguments:
        # 1. Local / Result (the file in your working directory)
        # 2. Base
        # 3. Remote
        with open(args.notebook[0], 'w') as resultfile:
            resultfile.write(json.dumps(pre_merged_notebook, indent=2))
    elif length == 4:
        # You need to run this before git mergetool will accept nbmerge
        # $ git config mergetool.nbmerge.cmd \
        #        "nbmerge \$LOCAL \$BASE \$REMOTE \$MERGED"
        # and then you can invoke it with:
        # $ git mergetool -t nbmerge
        #
        # Git gives four arguments (these are configurable):
        # 1. Local
        # 2. Base
        # 3. Remote
        # 4. Result (the file in your working directory)
        with open(args.notebook[3], 'w') as resultfile:
            resultfile.write(json.dumps(pre_merged_notebook, indent=2))
    else:
        # TODO save to the correct file in your working directory.
        print(json.dumps(pre_merged_notebook, indent=2))
