from pprint import pprint, pformat
import argparse

from parser_file import ParserFile
from lexer import Lexer
from parser_ import parse
import ast_ as ast

from validator import validate

PROGRAM_NAME = "mylang"
PROGRAM_VERSION = "0.0.1-dev0"

def parse_args():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME)
    
    parser.add_argument("-v", "--version", 
        action="version",
        version=f"{PROGRAM_NAME} {PROGRAM_VERSION}",
        help="prints the program version"
        )

    parser.add_argument("input_file",
        metavar="INPUT_FILE",
        default=None
    )

    parser.add_argument("-o",
        metavar="OUTPUT_FILE",
        default="out.s"
        )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    src = ParserFile(args.input_file)
    num_errors, ast = parse(args.input_file, src)

    if num_errors:
        print(f"Got {num_errors} error(s)")
        return 1
    
    pprint(ast)
    print("=============================")
    print("validating ...")
    validation_error = validate(src, ast)
    if not validation_error:
        print("Everything seems to be correct!")
    else:
        print("Something went wrong validaing!")
        return 1 
    return 0

if __name__ == "__main__": 
    raise SystemExit(main())

