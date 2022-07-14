import argparse


def add_run_args(parser, multiprocess=True):
    """
    Run command args
    """
    parser.add_argument(
        "-c", "--config_file", type=str, metavar="PATH", help="path to config file"
    )


# if __name__ == '__main__':
parser = argparse.ArgumentParser()
add_run_args(parser)
args = parser.parse_args()
