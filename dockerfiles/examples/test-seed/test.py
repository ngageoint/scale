import argparse
import json
import logging
import sys
import os

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG, stream=sys.stdout)


def run_algorithm(bytes_total, input_file, out_dir):
    """Read the indicated number of bytes from input file and store in output directory

    :param bytes_total:
    :param input_file:
    :param out_dir:
    :return:
    """

    bytes_read = 0
    chunk_size = 512

    logging.info('Reading %s bytes from %s and storing at %s.' % (bytes_total, input_file, out_dir))

    base_path = os.path.join(out_dir, 'output_file')
    os.makedirs(base_path)
    output_file = os.path.join(base_path, os.path.basename(input_file))
    logging.info('Data being stored in %s' % output_file)
    with open(input_file, 'rb') as infile:
        with open(output_file, 'wb') as outfile:
            while bytes_read <= bytes_total:
                if bytes_read + chunk_size > bytes_total:
                    chunk_size = bytes_total - bytes_read
                chunk = infile.read(chunk_size)

                # Break if EOF is encountered
                if not chunk: break

                outfile.write(chunk)
                bytes_read += chunk_size

    logging.info('Copy complete')

    return output_file

def validate_environment():
    """Check environment for the variables Seed executor should supply
    """
    expected_environment = [
        'OUTPUT_DIR',
        'ALLOCATED_CPUS',
        'ALLOCATED_MEM',
        'ALLOCATED_SHAREDMEM',
        'ALLOCATED_DISK',
        'INPUT_TEXT',
        'INPUT_FILES',
        'READ_LENGTH',
        'OUTPUT_COUNT',
        'DB_HOST',
        'DB_PASS'
    ]

    missing_keys = [x for x in expected_environment if x not in os.environ.keys()]
    if len(missing_keys):
        logging.critical('Missing expected environment values: \n%s' % '\n'.join(missing_keys))
        sys.exit(4)

if __name__ == '__main__':

    validate_environment()

    for key in os.environ.keys():
        logging.info("%30s %s" % (key,os.environ[key]))

    parser = argparse.ArgumentParser(description='Copy x number of bytes from input file to output file.')
    parser.add_argument('bytes_total', type=int, help='number of bytes to copy from input to output file')
    parser.add_argument('input_file', help='absolute path to input file')
    parser.add_argument('output_dir', help='absolute output directory path')
    args = parser.parse_args()

    logging.debug('Bytes to copy: {}'.format(args.bytes_total))
    logging.debug('Input file: {}'.format(args.input_file))
    logging.debug('Output directory: {}'.format(args.output_dir))

    output_file = run_algorithm(args.bytes_total, args.input_file, args.output_dir)

    # Write an output manifest for testing JSON property capture
    with open(os.path.join(args.output_dir, 'seed.outputs.json'), 'w') as output_json:
        input_size = os.path.getsize(args.input_file)
        contents = {'INPUT_FILE_NAME': args.input_file, 'INPUT_SIZE': input_size}
        json.dump(contents, output_json)

    sys.exit(0)
