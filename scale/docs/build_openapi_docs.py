"""Parses the given root directory and composes a complete OpenAPI specification file."""

import getopt
import os
import sys
import yaml


def build_openapi_docs(root_file, parse_dir):
    """Parses a directory of YAML files for OpenAPI chunks (paths, components, etc.) and injects them into
    the given root file and writes to the desired location.

    notes:
    - The given root_file MUST be prepopulated with `info` and `server` chunks
    - Only files ending in .yml or .yaml will be parsed
    - The following OpenAPI sections will be detected: paths, components, security, tags, externalDocs
    - If your root_file is in the parse_dir it will NOT be parsed

    inputs:
    - root_file - File path to the openapi.yaml file that parsed OpenAPI chunks will be attached to
    - parse_dir - The directory to parse for OpenAPI chunks

    outputs:
    - A complete OpenAPI spec written to the desired root_file
    """

    chunks = {
        'paths': {},
        'components': {
            'schemas': {}
        },
        'security': {},
        'tags': {},
        'externalDocs': {}
    }

    for _file in os.listdir(parse_dir):
        if _file == os.path.basename(root_file):
            continue

        if _file.endswith(".yml") or _file.endswith(".yaml"):
            with open(os.path.join(parse_dir, _file), 'r') as f:
                try:
                    yml = yaml.load(f)
                except yaml.scanner.ScannerError:
                    print ' '.join(["Error parsing file :", os.path.join(parse_dir, _file)])
                except yaml.parser.ParserError:
                    print ' '.join(["Error parsing file :", os.path.join(parse_dir, _file)])

                for chunk_type in chunks:
                    if chunk_type in yml:
                        c = yml[chunk_type]
                        for k, v in c.items():
                            if k == 'schemas':
                                s = yml[chunk_type][k]
                                for k, v in s.items():
                                    chunks[chunk_type]['schemas'][k] = v
                            else:
                                chunks[chunk_type][k] = v

    chunks = dict((k, v) for k, v in chunks.iteritems() if v)

    with open(root_file, 'a') as f:
        f.write(yaml.dump(chunks))

if __name__ == '__main__':
    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'f:p:', ['root_file=', 'parse_dir='])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-f', '--root_file'):
            root_file = arg
        elif opt in ('-p', '--parse_dir'):
            parse_dir = arg
        else:
            sys.exit(2)

    build_openapi_docs(root_file, parse_dir)

    sys.exit(0)
