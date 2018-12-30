import argparse
import json


def create_args_parser():
    prs = argparse.ArgumentParser(description='Write added matrix')
    prs.add_argument('first_matrix_name', help='A name for input json file with matrix')
    prs.add_argument('added_matrix_name', help='A name for json file with added matrix')
    return prs


def save_added_matrix(input_matrix_name, output_matrix_name):
    """
    Save added for input matrix in .json file with 'output_matrix_name' name
    """

    matrix = json.load(open(input_matrix_name, 'r'))['Matrix']

    # validation input matrix
    invalid_rows = [row for row in matrix if len(row) != len(matrix)]
    if invalid_rows:
        raise ArithmeticError('Incorrect matrix input. Matrix should be squared')

    added_matrix = list(zip(*matrix))
    json.dump(added_matrix, open(output_matrix_name, 'w'))


if __name__ == "__main__":
    parser = create_args_parser()
    args = parser.parse_args()
    save_added_matrix(args.first_matrix_name, args.added_matrix_name)
