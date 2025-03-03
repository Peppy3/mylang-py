from pprint import pprint, pformat
import argparse

from parser_file import ParserFile
from lexer import Lexer
from parser_ import parse
import ast_ as ast
from typecheck import Typechecker

from ir import generator

PROGRAM_NAME = "mylang"
PROGRAM_VERSION = "0.0.1-dev0"


def parse_args():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME)

    parser.add_argument("-v", "--version",
        action="version",
        version=f"{PROGRAM_NAME} {PROGRAM_VERSION}",
        help="prints the program version"
        )

    parser.add_argument("--dump",
        choices=("ast",),
        help="dumps to the stdout",
        )

    parser.add_argument("-o",
        metavar="OUTPUT_FILE",
        default="out.s"
        )

    parser.add_argument("input_file",
        metavar="INPUT_FILE",
        default=None
        )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    src = ParserFile(args.input_file)
    ast, num_errors = parse(args.input_file, src)

    if num_errors:
        print(f"Got {num_errors} error(s)")
        return 1
    
    if args.dump == "ast":
        pprint(ast)
        # return 0


    typechecker = Typechecker(src)
    typechecker.typecheck(ast)

    # print("=============================")
    # print("generating IR ...")
    #
    # num_errors, rep = generator.generate(src, ast)
    # if num_errors:
    #     print(f"Got {num_errors} error(s) when generating IR")
    #     return 1 

    # print("Passed IR generation")

    return 0


if __name__ == "__main__": 
    raise SystemExit(main())

