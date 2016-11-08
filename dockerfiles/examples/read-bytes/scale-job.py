import argparse
import logging
import sys
import json
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

    output_file = os.path.join(out_dir, os.path.basename(input_file))
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

# Capture results in manifest
def generate_results_manifest(output_dir, output_file):
    json_dict = {}
    json_dict['version'] = '1.1'
    json_dict['output_data'] = []

    file_dict = {}
    file_dict['name'] = 'output_file'
    file_dict['file'] = {'path': output_file}
    json_dict['output_data'].append(file_dict)

    with open(os.path.join(output_dir, 'results_manifest.json'), 'w') as outfile:
        json.dump(json_dict, outfile)

    logging.info('Completed manifest creation')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy x number of bytes from input file to output file.')
    parser.add_argument('bytes_total', type=int, help='number of bytes to copy from input to output file')
    parser.add_argument('input_file', help='absolute path to input file')
    parser.add_argument('output_dir', help='absolute output directory path')
    args = parser.parse_args()

    logging.debug('Bytes to copy: {}'.format(args.bytes_total))
    logging.debug('Input file: {}'.format(args.input_file))
    logging.debug('Output directory: {}'.format(args.output_dir))

    output_file = run_algorithm(args.bytes_total, args.input_file, args.output_dir)
    generate_results_manifest(args.output_dir, output_file)

    sys.exit(0)
