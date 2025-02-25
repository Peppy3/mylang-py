from pprint import pprint
from tokens import Token, TokenEnum
from parser_file import ParserFile
import ast_ as ast

VALIDATOR_DEBUG: bool = False
validator_debug_uid: int = 0

def validate_func(func):
    if VALIDATOR_DEBUG:
        def f(*args):
            global validator_debug_uid
            uid = validator_debug_uid
            validator_debug_uid += 1
            print(f"validator START: {func.__name__}", uid)
            ret = func(*args)
            print(f"validator END: {func.__name__}", uid)
            return ret
        return f
    return func

class Validator:
    __slots__ = ("src",)
    def __init__(self, src):
        self.src = src
    
    validate = lambda self, ast: self.module(ast)

    @validate_func
    def type_expr(self, node: ast.Node) -> bool:

        if node.isa(ast.Literal) and node.token.type == TokenEnum.Identifier:
            return False
        elif node.isa(ast.FuncType):
            error = False
            for arg in node.args:
                error |= self.declaration(arg)
            if not error:
                return error
            return self.type_expr(node.ret)
        elif node.isa(ast.UnaryExpr):
            if node.op != TokenEnum.Asterisk:
                return True
            return self.type_expr(node.expr)
        elif node.isa(ast.BinaryExpr):
            # FIXME: print an error
            return False
        else:
            raise NotImplementedError(node.__class__.__name__)

    @validate_func
    def expression(self, node: ast.Node) -> bool:
        if node.isa(ast.Literal):
            return False 
        elif node.isa(ast.BinaryExpr):
            return self.expression(node.lhs) and self.expression(node.rhs)
        elif node.isa(ast.PostfixExpr):
            return self.expression(node.expr)
        elif node.isa(ast.UnaryExpr):
            return self.expression(node.expr)
        elif node.isa(ast.FuncType):
            error = False
            for arg in node.args:
                error |= self.declaration(arg)
            return error
        
        raise NotImplementedError(node.__class__.__name__)

    @validate_func
    def declaration(self, node: ast.Node) -> bool:
        if not self.type_expr(node.type_expr):
            return True
        if node.expr is None:
            return False
        return self.expression(node.expr)

    @validate_func
    def statement(self, node: ast.Node) -> bool:
        
        if node.isa(ast.Declaration):
            return self.declaration(node)
        pprint(node)

        raise NotImplementedError(node.__class__.__name__)

    @validate_func
    def module(self, node: ast.Node) -> bool:
        error = False
        for stmt in node.statements:
            error |= self.statement(stmt)
        return error

def validate(src: ParserFile, ast: ast.Node):
    validator = Validator(src)
    return validator.validate(ast)


