import argparse
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

    sys.exit(0)
