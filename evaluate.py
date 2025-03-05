import ast_ as ast
from tokens import TokenEnum

class Evaluator:
    def __init__(self, src):
        self.src = src

    def math(self, node):
        if node.isa(ast.BinaryExpr):
            lhs = self.math(node.lhs)
            rhs = self.math(node.rhs)

            if node.op == TokenEnum.Addition:
                return lhs + rhs
            elif node.op == TokenEnum.Subtraction:
                return lhs - rhs
            elif node.op == TokenEnum.Division:
                return lhs / rhs
            elif node.op == TokenEnum.Asterisk:
                return lhs * rhs
            elif node.op == TokenEnum.Modulo:
                return lhs % rhs

            elif node.op == TokenEnum.Xor:
                return lhs ^ rhs
            elif node.op == TokenEnum.Ampersand:
                return lhs & rhs
            elif node.op == TokenEnum.Pipe:
                return lhs | rhs

            elif node.op == TokenEnum.ShiftLeft:
                return lhs << rhs
            elif node.op == TokenEnum.ShiftRight:
                return lhs >> rhs
        
        elif node.isa(ast.UnaryExpr):
            val = self.math(node.expr)
            if node.op == TokenEnum.Increment:
                return val + 1
            elif node.op == TokenEnum.Decrement:
                return val - 1
            elif node.op == TokenEnum.Not:
                return ~val

        elif node.isa(ast.PostfixExpr):
            return self.math(node.expr)

        elif node.isa(ast.Literal):
            return int(self.src.get_token_string(node.token))
