from tokens import Token, TokenEnum
import ast_ as ast
from symbol_table import SymbolTable
from collections import abc
from evaluate import Evaluator

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
    __slots__ = "name", "symbols"
    def __init__(self, name: str, symbols: SymbolTable):
        self.name = name
        self.symbols = symbols

    def __eq__(self, other):
        if not isinstance(other, StructType):
            return False

        for s1, s2 in zip(self.symbols.values(), other.symbols.values()):
            if s1 != s2:
                return False

        return True

    def lookup(self, name: str):
        return self.symbols.get(name)

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
    __slots__ = "length", "type"
    def __init__(self, typ, length=None):
        self.type = typ
        self.length = length

    def __eq__(self, other):
        if not isinstance(other, SliceType):
            return False

        if self.len is None:
            return True
        
        # allow to create and convert to a bigger slice but not the other way around
        return self.len >= other.len

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
    __slots__ = "symbol_stack", "block_stack", "src", "num_errors", "evaluator"
    def __init__(self, src):
        self.symbol_stack = [SymbolTable(BUILTIN_TYPES)]
        self.block_stack = []
        self.src = src
        self.num_errors = 0
        self.evaluator = Evaluator(self.src)

        
    def error(self, token, msg):
        self.num_errors += 1
        self.src.error(token, msg)
    

    def lookup(self, name):
        for table in reversed(self.symbol_stack):
            symbol = table.get(name)
            if symbol[1] is not None:
                return symbol

        return None


    def insert(self, name, val):
        self.symbol_stack[-1].insert(name, val)
    

    def type_expression(self, node, is_ptr=False):
        if node.isa(ast.Identifier):
            name = self.src.get_token_string(node.token)
            
            _, typ = self.lookup(name)
            
            if (not is_ptr) and typ.isa(StructType) and len(self.block_stack):
                stack_top = self.block_stack[-1]
                if stack_top.isa(StructType) and name == stack_top.name:
                    self.error(node.token, f"{name!r} is can not be a recursive datastructure")
                    return None

            if typ is None:
                self.error(node.token, f"Could not resolve type {name!r}")
                return None
            return typ
        elif node.isa(ast.FuncType):
            ret_type = self.type_expression(node.ret)
            func_type = FuncType(ret_type, list())

            self.block_stack.append(func_type)
            
            for arg in node.args:
                name = self.src.get_token_string(arg.name)
                arg_type = self.type_expression(arg.type_expr)
                func_type.append_arg(name, arg_type)

            self.block_stack.pop()

            return func_type

        elif node.isa(ast.UnaryExpr):
            if node.op == TokenEnum.Asterisk:
                typ = self.type_expression(node.expr, is_ptr=True)
                return PointerType(typ)
            else:
                self.error(node.op, f"Unary {node.op.type.name} not allowed in type expressions")
        elif node.isa(ast.Slice):
            member_typ = self.type_expression(node.expr)

            if node.subscript is None:
                return SliceType(member_typ)
            else:
                size = self.evaluator.math(node.subscript)
                return SliceType(member_typ, size)
        else:
            raise NotImplementedError(node)


    def expression(self, node):
        if node.isa(ast.Identifier):
            name = self.src.get_token_string(node.token)
            _, val = self.lookup(name)

            if val is None:
                self.error(node.token, f"Could not reslolve value {name!r}")

            return val

        elif node.isa(ast.Slice):
            val = self.expression(node.expr)
            
            subscript = self.expression(node.subscript)

            if not (subscript.isa(UintType) or subscript.isa(IntType)):
                self.error(node.subscript, "value must get evaluated to an integer type")

            return val.type

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

            if node.op == TokenEnum.Period:
                lhs = self.expression(node.lhs)

                if not lhs.isa(StructType):
                    self.error(node.op, "Can only do member access on struct types")

                member_name = self.src.get_token_string(node.rhs)
                _, member_type = lhs.lookup(member_name)

                if member_type is None:
                    self.error(node.rhs, f"{member_name!r} is not a member of {lhs.name!r}")
                return member_type

            lhs = self.expression(node.lhs)
            rhs = self.expression(node.rhs)

            if lhs is None or rhs is None:
                return None

            if lhs.isa(PointerType) or rhs.isa(PointerType):
                self.error(node.op, f"No pointer arithmatic allowed")
                return None
            elif lhs.isa(FuncType) or rhs.isa(FuncType):
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
                return SliceType(UintType(8), node.token.length)
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
                    self.error(node.expr, "Function can only be initialised to a code block")
                    return

                self.symbol_stack.append(SymbolTable())
                self.block_stack.append(name)

                for arg in typ.args: # tuple[name, Type]
                    self.insert(*arg)

                for expr in node.expr.statements:
                    self.statement(expr)

                self.block_stack.pop()
                self.symbol_stack.pop()
                return
            
            # might not have an assignment
            if node.expr is None:
                return

            val = self.expression(node.expr)
            if val is None:
                return
            elif (typ.isa(IntType) or typ.isa(UintType)) and (val.isa(IntType) or val.isa(UintType)):
                return
            elif typ.isa(SliceType) and val.isa(SliceType):
                # allow for slice type lengths that are greater or equal than the actual value
                if typ.length is not None and typ.length < val.length:
                    self.error(node.type_expr.left_square, f"Slice must be a length of {val.length} or greater")
                else:
                    typ = val
                return
            else:
                self.error(node.expr, "value does not have same type as declared variable")
        elif node.isa(ast.ReturnStmt):
            expr = self.expression(node.expr)

            assert len(self.block_stack) > 0
            
            _, func_type = self.lookup(self.block_stack[-1])
            if expr != func_type.ret:
                self.error(node,
                    "Value does not have the same type as function return value")
                return
        else:
            return self.expression(node)


    def compound_type(self, node):
        name = "anonymus"
        if node.name is not None:
            name = self.src.get_token_string(node.name)

        if node.which != TokenEnum.Struct:
            raise NotImplementedError("node.which != TokenEnum.Struct")
        
        struct = StructType(name, SymbolTable())

        self.insert(name, struct)

        self.symbol_stack.append(struct.symbols)
        self.block_stack.append(struct)

        for decl in node.members.statements:
            if decl.isa(ast.Declaration):
                self.statement(decl)
            else:
                NotImplementedError(f"node.members[i].isa({decl})")

        self.block_stack.pop()
        self.symbol_stack.pop()


    def module(self, node):
        for stmt in node.statements:
            if stmt.isa(ast.Declaration):
                self.statement(stmt)
            elif stmt.isa(ast.CompoundType):
                if stmt.name is None:
                    self.error(stmt, "Module scope can not have anonymus structs")
                self.compound_type(stmt)
            elif stmt.isa(ast.BinaryExpr):
                self.error(stmt.op, "Module scope can only have declarations")
            else:
                raise NotImplementedError(f"module scope error for {stmt}")


    def typecheck(self, ast):
        
        self.module(ast)

        # == 1 because of builtins is in its own table
        assert len(self.symbol_stack) == 1, "Something left on the stack"

        assert len(self.block_stack) == 0

        return self.num_errors



def validate_and_resolve_types(src, ast):
    num_errors = Typechecker(src).typecheck(ast)
    
    return num_errors

