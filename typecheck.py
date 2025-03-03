from tokens import Token, TokenEnum
import ast_ as ast
from symbol_table import SymbolTable
from collections import abc

class Type:
    def __eq__(self, other):
        return isinstance(other, Type) and self.__class__ == other.__class__
 
    def isa(self, cls):
        return isinstance(self, cls)

    __repr__ = lambda self: self.__class__.__name__


class PointerType(Type):
    __slots__ = ("to",)
    def __init__(self, to):
        self.to = to

    __str__ = lambda self: f"*{str(self.to)}"
    __eq__ = lambda self, other: isinstance(other, Pointer) and self.to == other.to

class BlockType(Type):
    __str__ = lambda self: "block"

class TypeType(Type):
    __str__ = lambda self: "type"

class BoolType(Type):
    __str__ = lambda self: "bool"

class VoidType(Type):
    __str__ = lambda self: "void"

class StructType(Type):
    __str__ = lambda self: "struct"

class IntType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, bit_length: int | None = None):
        self.bit_length = bit_length
    
    def __str__(self):
        return "int" if self.bit_length is None else f"i{self.bit_length}"

    def __eq__(self, other):
        if self.bit_length is None:
            return True
        return isinstance(other, IntType) and self.bit_length == other.bit_length

class UintType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, bit_length: int | None = None):
        self.bit_length = bit_length
    
    def __str__(self):
        return "uint" if self.bit_length is None else f"u{self.bit_length}"

    def __eq__(self, other):
        if self.bit_length is None:
            return True
        return isinstance(other, UintType) and self.bit_length == other.bit_length

class FloatType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, bit_length=64):
        self.bit_length = bit_length
    
    __str__ = lambda self: f"f{self.bit_length}"

    def __eq__(self, other):
        if self.bit_length is None:
            return True
        return isinstance(other, FloatType) and self.bit_length == other.bit_length

class FuncType(Type):
    __slots__ = "ret", "args"
    def __init__(self, ret, args):
        self.ret = ret
        self.args = args

    def __repr__(self):
        gen = (arg.name if isinstance(arg, Block) else str(arg) for arg in self.args)
        return "(" + ", ".join(gen) + f") -> {self.ret}" 

    def __eq__(self, other):
        if not isinstance(other, FuncType) or self.ret != other.ret:
            return False
            
        if len(self.args) != len(other.args):
            return False
        
        for s_arg, o_arg in zip(self.args, other.args):
            if s_arg != o_arg:
                return False
        
        return True

    def append_arg(self, name, typ):
        self.args.append((name, typ))


class SliceType(Type):
    __slots__ = "len", "type"
    def __init__(self, typ, length):
        self.type = typ
        self.len = length

    __str__ = lambda self: f"{str(self.type)}[{self.len}]"


BUILTIN_TYPES: list = [
    ("i8", IntType(8)),
    ("i16", IntType(16)),
    ("i32", IntType(32)),
    ("i64", IntType(64)),
    ("int", IntType(None)),

    ("u8", UintType(8)),
    ("u16", UintType(16)),
    ("u32", UintType(32)),
    ("u64", UintType(64)),
    ("uint", UintType(None)),

    ("f16", FloatType(16)),
    ("f32", FloatType(32)),
    ("f64", FloatType(64)),
]

class Typechecker:
    __slots__ = "symbol_stack", "func_stack", "src", "num_errors"
    def __init__(self, src):
        self.symbol_stack = [SymbolTable(BUILTIN_TYPES)]
        self.func_stack = [] # only used for return statements
        self.src = src
        self.num_errors = 0

        
    def error(self, token, msg):
        self.num_errors += 1
        self.src.error(token, msg)
    

    def lookup(self, name):
        for table in reversed(self.symbol_stack):
            if (symbol := table.get(name)) is not None:
                return symbol
        return None


    def insert(self, name, val):
        self.symbol_stack[-1].insert(name, val)


    def type_expression(self, node):
        if node.isa(ast.Identifier):
            name = self.src.get_token_string(node.token)
            typ = self.lookup(name)

            if typ is None:
                self.error(node.token, f"Could not resolve type {name!r}")
                return None
            return typ
        elif node.isa(ast.FuncType):
            ret_type = self.type_expression(node.ret)
            func_type = FuncType(ret_type, list())
            
            for arg in node.args:
                name = self.src.get_token_string(arg.name)
                arg_type = self.type_expression(arg.type_expr)
                func_type.append_arg(name, arg_type)

            return func_type
        elif node.isa(ast.UnaryExpr):
            if node.op == TokenEnum.Asterisk:
                typ = self.type_expression(node.expr)
                return PointerType(typ)
            else:
                self.error(node.op, f"Unary {node.op.type.name} not allowed in type expressions")
        else:
            raise NotImplementedError(node)


    def expression(self, node):
        if node.isa(ast.Identifier):
            name = self.src.get_token_string(node.token)
            val = self.lookup(name)

            if val is None:
                self.error(node.token, f"Could not reslolve value {name!r}")

            return val

        elif node.isa(ast.CallExpr):
            val = self.expression(node.func)

            if val is None:
                return None

            if not val.isa(FuncType):
                self.error(node.func, f"{name!r} is not a function")
                return None
            
            func_arg_len = len(val.args)
            call_arg_len = len(node.args)
            if func_arg_len != call_arg_len:
                self.error(node.func,
                    f"Expected {func_arg_len} arguments to function but got {call_arg_len}")
                return None
            
            for call_arg, func_arg in zip(node.args, val.args):
                expr = self.expression(call_arg)
                if expr is None: 
                    continue
                
                if expr != func_arg[1]:
                    self.error(call_arg, 
                        "Function argument type does not match the definition. "
                        f"Expected {func_arg[1]}")

            return val.ret

        elif node.isa(ast.BinaryExpr):
            lhs = self.expression(node.lhs)
            rhs = self.expression(node.rhs)

            if lhs is None or rhs is None:
                return None

            if isinstance(lhs, PointerType) or isinstance(rhs, PointerType):
                self.error(node.op, f"No pointer arithmatic allowed")
                return None
            elif isinstance(lhs, FuncType) or isinstance(rhs, FuncType):
                self.error(node.op, f"Can not use binary operator on a function")
                return None

            if node.op == TokenEnum.Addition:
                if lhs != rhs:
                    self.error(node.op, f"lhs does not have the same type as rhs")
                    return None
                return lhs
            elif node.op == TokenEnum.Asterisk:
                if lhs != rhs:
                    self.error(node.op, f"lhs does not have the same type as rhs")
                    return None
                return lhs
            else:
                raise NotImplementedError(node.op)
        elif node.isa(ast.Literal):
            if node.token == TokenEnum.IntegerLiteral:
                return IntType(None)
            elif node.token == TokenEnum.StringLiteral:
                return SliceType(UintType(node.token, 8), node.token.length)
            elif node.token == TokenEnum.FloatLiteral:
                return FloatType(None)
            else:
                raise NotImplementedError(node.token)
        else:
            raise NotImplementedError(node)


    def statement(self, node):
        if node.isa(ast.Declaration):
            name = self.src.get_token_string(node.name)
            typ = self.type_expression(node.type_expr)

            self.insert(name, typ)

            if node.expr is None or typ is None:
                return

            if typ.isa(FuncType):
                if not node.expr.isa(ast.CodeBlock):
                    self.error(node.name, "Function should be initialised to a code block")
                    return

                self.symbol_stack.append(SymbolTable())
                self.func_stack.append(typ)

                for arg in typ.args: # Tuple[name, Type]
                    self.insert(*arg)

                for expr in node.expr.statements:
                    self.statement(expr)

                self.func_stack.pop()
                self.symbol_stack.pop()
                return
            
            #if node.expr.isa(ast.CodeBlock):
            #    self.symbol_stack.append(SymbolTable())
            #    for expr in node.expr.statements:
            #        self.statement(expr)
            #    self.symbol_stack.pop()
            #    return

            val = self.statement(node.expr)
            if (typ.isa(IntType) or typ.isa(UintType)) and (val.isa(IntType) or val.isa(UintType)):
                return

            self.error(node.expr.token, f"value does not have same type as declared variable")
        elif node.isa(ast.ReturnStmt):
            expr = self.expression(node.expr)
            
            if expr != self.func_stack[-1].ret:
                self.error(node.return_token,
                    "Value does not have the same type as function return value")
                return
        else:
            return self.expression(node)


    def module(self, node):
        for stmt in node.statements:
            if stmt.isa(ast.Declaration):
                self.statement(stmt)
            elif stmt.isa(ast.BinaryExpr):
                self.error(stmt.op, "Module scope can only have declarations")
            else:
                raise NotImplementedError(f"module scope error for {stmt}")


    def typecheck(self, ast):
        
        self.module(ast)

        # == 1 because of builtins is in its own table
        assert len(self.symbol_stack) == 1, "Something left on the stack"

        assert len(self.func_stack) == 0

        return self.num_errors



def validate_and_resolve_types(src, ast):
    num_errors = Typechecker(src).typecheck(ast)
    
    return num_errors

