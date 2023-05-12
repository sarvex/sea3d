#!/usr/bin/env python

import sys

if sys.version_info < (2, 7):
    print("This script requires at least Python 2.7.")
    print("Please, update to a newer version: http://www.python.org/download/releases/")
    exit()

import argparse
import json
import os
import shutil
import tempfile

def make_parent_directories_if_needed(filepath):
    parent_directory = os.path.dirname(os.path.realpath(filepath))
    try:
        os.makedirs(parent_directory)
    except OSError:
        pass # nothing to do

def main(argv=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('--include', action='append', required=True)
    parser.add_argument('--externs', action='append', default=['common.js'])
    parser.add_argument('--amd', action='store_true', default=False)
    parser.add_argument('--minify', action='store_true', default=False)
    parser.add_argument('--nocheckvars', action='store_true', default=False)
    parser.add_argument('--output', default='')
    parser.add_argument('--sourcemaps', action='store_true', default=False)

    args = parser.parse_args()

    output = args.output
    make_parent_directories_if_needed(output) # necessary

    # merge

    print(f' * Building {output}')

    # enable sourcemaps support

    if args.sourcemaps:
        sourcemap = f'{output}.map'
        sourcemapping = '\n//@ sourceMappingURL=' + sourcemap
        sourcemapargs = f' --create_source_map {sourcemap} --source_map_format=V3'
    else:
        sourcemap = sourcemapping = sourcemapargs = ''

    fd, path = tempfile.mkstemp()
    with open(path, 'w') as tmp:
        sources = []

        if args.amd:
            tmp.write('( function ( root, factory ) {\n\n\tif ( typeof define === \'function\' && define.amd ) {\n\n\t\tdefine( [ \'exports\' ], factory );\n\n\t} else if ( typeof exports === \'object\' ) {\n\n\t\tfactory( exports );\n\n\t} else {\n\n\t\tfactory( root );\n\n\t}\n\n}( this, function ( exports ) {\n\n')

        for include in args.include:
            with open(f'{include}.json', 'r') as f:
                files = json.load(f)
            for filename in files:
                filename = f'../{filename}';
                sources.append(filename)
                with open(filename, 'r') as f:
                    tmp.write(f.read())
                    tmp.write('\n')

        if args.amd:
            tmp.write('exports.UIL = UIL;\n\n} ) );')

    # save

    if args.minify is False:
        shutil.copy(path, output)
        os.chmod(output, 0o664); # temp files would usually get 0600

    else:

        externs = ' --externs '.join(args.externs)
        nocheckvars = "--jscomp_off=checkVars" if args.nocheckvars is True else ""
        source = ' '.join(sources)
        cmd = f'java -jar closure-compiler/closure-compiler-v20161024.jar --warning_level=VERBOSE --jscomp_off=globalThis {nocheckvars} --externs {externs} --jscomp_off=checkTypes --language_in=ECMASCRIPT5_STRICT --js {source} --js_output_file {output} {sourcemapargs}'
        os.system(cmd)

        # header

        with open(output,'r') as f: text = f.read()
        with open(output,'w') as f: f.write(text + sourcemapping)

    os.close(fd)
    os.remove(path)


if __name__ == "__main__":
    main()