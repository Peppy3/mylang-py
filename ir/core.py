from enum import Enum, auto
from weakref import proxy

# all operations should start with (OpEnum, ast.Node, is_type_expr, ...)
class OpEnum(Enum):
    # simple no operation (probably not needed)
    NOP = auto()

    # (..., name)
    MODULE = auto()
    # (..., is_type_expr=False, name, typ, val)
    VAR_DECL = auto()
    # (..., name, ret_val, args: list[(name, type)], body: list | None)
    FUNC_DECL = auto()

    # (..., ret, typ_expr, is_raw, length: int | None)
    SLICE_TYPE = auto()
    # (..., which, name, block)
    COMPOUND_TYPE = auto()
    # (..., ret, expr)
    POINTER_TYPE = auto()

    # (..., ret_val: uid | None)
    RETURN_STMT = auto()

    # (..., ret, args: list[arg, arg, ...])
    FUNC_CALL = auto()

    # (..., slice, idx: uid)
    SLICE_INDEXING = auto()

    # Binary operations
    # (..., ret, lhs, rhs)
    BIN_ADD = auto()
    BIN_MUL = auto()
    MEMBER_ACCESS = auto()


# just a tuple (there is no decently fast way to type this)
def Instr(*args):
    return tuple(args)

class Type:
    __slots__ = ("token",)
    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return isinstance(other, Type) and self.__class__ == other.__class__
    
    __repr__ = lambda self: self.__class__.__name__


class PointerType(Type):
    __slots__ = ("to",)
    def __init__(self, token, to):
        super().__init__(token)
        self.to = to
    __str__ = lambda self: f"*{str(self.to)}"
    __eq__ = lambda self, other: isinstance(other, Pointer) and self.to == other.to

class ModuleType(Type):
    def __init__(self, token):
        super().__init__(token)

class BlockType(Type):
    def __init__(self, token):
        super().__init__(token)

class TypeType(Type):
    def __init__(self, token):
        super().__init__(token)

class BoolType(Type):
    def __init__(self, token):
        super().__init__(token)

class VoidType(Type):
    def __init__(self, token):
        super().__init__(token)

class StructType(Type):
    def __init__(self, token):
        super().__init__(token)
    
    __str__ = lambda self: "struct"

class IntType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"i{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, IntType) and self.bit_length == other.bit_length

class UintType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"u{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, UintType) and self.bit_length == other.bit_length

class FloatType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"f{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, FloatType) and self.bit_length == other.bit_length

class FuncType(Type):
    def __init__(self, ret, args):
        self.ret = ret
        self.args = args

    def __repr__(self):
        gen = (arg.name if isinstance(arg, Block) else str(arg) for arg in self.args)
        return "(" + ", ".join(gen) + f") -> {self.ret}" 

class SliceType(Type):
    __slots__ = "len", "type"
    def __init__(self, token, typ, length):
        super().__init__(token)
        self.type = typ
        self.len = length

    __str__ = lambda self: f"{str(self.type)}[{self.len}]"

class Value:
    __slots__ = "token", "type", "name"
    def __init__(self, token, name, typ):
        self.token = token
        self.name = name

    ref = lambda self: self

    __hash__ = lambda self: hash(self.name)
    __str__ = lambda self: f"%{self.name} {self.type}"

class Constant(Type):
    __slots__ = "token", "type", "const"
    def __init__(self, token, typ, const):
        self.token = token
        self.type = typ
        self.const = const

    __repr__ = lambda self: str(self.const)

class Block:
    def __init__(self, parent_block):
        self.parent = parent_block
        self.symbols = SymbolTable()
        self.instr_list = list()
        self.next_uid = 0

    __len__ = lambda self: len(self.instr_list)
    __hash__ = lambda self: hash(self.name)
    __str__ = lambda self: str(self.type)

    def dissasemble(self): 
        s = f"\n\n{self.name}:\n"
        s += str(self.symbols) + "\n"
        s += "\n".join(repr(instr) for instr in self.instr_list)
        return s + "\n"

    def __enter__(self): 
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def gen_uid_or_name(self, name: str | None):
        if name is None:
            name = str(self.next_uid)
            self.next_uid += 1
        return name

    def value(self, token, typ, name=None):
        name = self.gen_uid_or_name(name)
        return self.symbols.insert(Value(token, name, typ))

    def block(self, typ, name=None):
        name = self.gen_uid_or_name(name)
        return self.symbols.insert(Block(typ, proxy(self), name))

    def lookup(self, name):
        if (val := self.symbols.get(name)) is not None:
            return val
        elif self.parent is not None:
            return self.parent.lookup(name)
        else:
            return None


if __name__ == "__main__":

    main_module = Block(None)

    val1 = main_module.build_add(Constant(None, IntType(None), 42), Constant(None, IntType(None), 27))
    main_module.build_ret(val1)
    
    print(main_module)

