"""Parses the given root directory and composes a complete OpenAPI specification file."""

import getopt
import os
import sys
import yaml

def build_openapi_docs(root_file, parse_dir, dest_dir):
    """Parses a directory of YAML files for OpenAPI chunks (paths, components, etc.) and injects them into
    the given root file and writes to the desired location.

    notes:
    - The given root_file MUST be prepopulated with `info` and `server` chunks
    - Only files ending in .yml or .yaml will be parsed
    - The following OpenAPI sections will be detected: paths, components, security, tags, externalDocs
    
    inputs:
    - root_file - File path to the openapi.yaml file that parsed OpenAPI chunks will be attached to
    - parse_dir - The directory to parse for OpenAPI chunks
    - dest_dir - The directory that the resulting openapi.yml will be written to

    outputs:
    - A complete OpenAPI spec written to the desired directory 
    """

    chunks = {
        'paths': [],
        'components': [],
        'security': [],
        'tags': [],
        'externalDocs': []
    }

    for file in os.listdir(parse_dir):
        if file.endswith(".yml") or file.endswith(".yaml"):
            with open(os.path.join(parse_dir, file), 'r') as f:
                try:
                    yml = yaml.load(f)
                except yaml.scanner.ScannerError:
                    print ' '.join(["Error parsing file :", os.path.join(parse_dir, file)])
                except yaml.parser.ParserError:
                    print ' '.join(["Error parsing file :", os.path.join(parse_dir, file)])
                print(type(yml))


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:p:d', ['root_file=', 'parse_dir=', 'dest_dir'])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-f', '--root_file'):
            root_file = arg
        elif opt in ('-p', '--parse_dir'):
            parse_dir = arg
        elif opt in ('-d', '--dest_dir'):
            dest_dir = arg
        else:
            sys.exit(2)
    
    build_openapi_docs(root_file, parse_dir, dest_dir)

    sys.exit(0)