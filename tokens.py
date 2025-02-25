from enum import IntEnum, auto
from dataclasses import dataclass

class TokenEnum(IntEnum):
    Invalid = auto()
    Eof = auto()

    Equal = auto()              # ==
    NotEqual = auto()           # !=
    LessThan = auto()           # <
    GreaterThan = auto()        # >
    LessThanOrEqual = auto()    # <=
    GreaterThanOrEqual = auto() # >=

    BoolNot = auto()    # not
    BoolAnd = auto()    # and
    BoolOr = auto()     # or

    Increment = auto()  # ++
    Decrement = auto()  # --

    Addition = auto()       # +
    Subtraction = auto()    # -
    Asterisk = auto()       # *
    Division = auto()       # /
    Modulo = auto()         # %

    Not = auto()        # ~
    Xor = auto()        # ^
    Ampersand = auto()  # &
    Pipe = auto()       # |

    ShiftLeft = auto()  # <<
    ShiftRight = auto() # >>

    Period = auto()     # .
    Ellipsis = auto()   # ...
    Arrow = auto()      # ->
    Comma = auto()      # ,

    Semicolon = auto()  # ;
    Colon = auto()      # :
    Address = auto()    # @

    ASSIGNMENT_START = auto()
    Assignment = auto()         # =
    AssignAdd = auto()          # +=
    AssignSub = auto()          # -=
    AssignMul = auto()          # *=
    AssignDiv = auto()          # /=
    AssignMod = auto()          # %=
    AssignShiftLeft = auto()    # <<=
    AssignShiftRight = auto()   # >>=

    AssignNot = auto()  # ~=
    AssignXor = auto()  # ^=
    AssignAnd = auto()  # &=
    AssignPipe = auto() # |=
    ASSIGNMENT_END = auto()

    LeftParen = auto()      # (
    RightParen = auto()     # )
    LeftCurly = auto()      # {
    RightCurly = auto()     # }
    LeftSquare = auto()     # [
    RightSquare = auto()    # ]

    If = auto()
    Else = auto()

    Switch = auto()
    Case = auto()
    Default = auto()

    While = auto()
    For = auto()
    Continue = auto()
    Break = auto()
    Return = auto()
    Goto = auto()

    Pub = auto()
    Const = auto()
    Macro = auto()
    Extern = auto()
    Inline = auto()

    Module = auto()
    Import = auto()
    As = auto()

    Struct = auto()
    Union = auto()
    Enum = auto()

    Null = auto()
    true = auto()
    false = auto()

    Identifier = auto()
    IntegerLiteral = auto()
    HexLiteral = auto()
    FloatLiteral = auto()
    CharLiteral = auto()
    StringLiteral = auto()

@dataclass(slots=True, frozen=True, repr=True)
class Token:
    type: TokenEnum
    pos: int
    length: int

    def precedence(self):
        if self.type == TokenEnum.BoolOr:
            return 1
        elif self.type == TokenEnum.BoolAnd:
            return 2
        elif self.type in (
            TokenEnum.Equal, TokenEnum.NotEqual, 
            TokenEnum.LessThan, TokenEnum.GreaterThan,
            TokenEnum.LessThanOrEqual, TokenEnum.GreaterThanOrEqual
            ):
            return 3
        elif self.type in (
            TokenEnum.Addition, TokenEnum.Subtraction,
            TokenEnum.Pipe, TokenEnum.Xor
            ):
            return 4
        elif self.type in (
            TokenEnum.Asterisk, TokenEnum.Division, TokenEnum.Modulo,
            TokenEnum.ShiftLeft, TokenEnum.ShiftRight, TokenEnum.Ampersand
            ):
            return 5
        else:
            return 0
    
    def is_unary(self):
        return self.type in (
            TokenEnum.Increment,
            TokenEnum.Decrement,
            TokenEnum.Subtraction,
            TokenEnum.Asterisk,
            TokenEnum.Not,
            TokenEnum.BoolNot,
            TokenEnum.Ampersand
            )

    def is_literal(self):
        return self.type in (
            TokenEnum.IntegerLiteral,
            TokenEnum.HexLiteral,
            TokenEnum.FloatLiteral,
            TokenEnum.CharLiteral,
            TokenEnum.StringLiteral,
        )


