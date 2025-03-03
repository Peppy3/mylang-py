from abc import ABC, abstractmethod
from dataclasses import dataclass

from tokens import Token

def walk_func(func):
    def f(self, visitor):
        visitor = visitor.visit(self)
        if visitor is None: 
            return None
        func(self, visitor)
        visitor.visit(None)

    return f

def walk_list(l, visitor):
    for node in l:
        visitor.visit(node)

class Node(ABC):
    @abstractmethod
    def walk(self, visitor):
        ...
    
    @abstractmethod
    def pos(self) -> int: # gives the start position of the node
        ...

    @abstractmethod
    def end(self) -> int : # gives one position past the end of the node
        ...

    def __str__(self):
        return f"ast.{self.__class__.__name__}"

    def isa(self, cls):
        return isinstance(self, cls)


@dataclass(slots=True, repr=True)
class Identifier(Node):
    token: Token

    @walk_func
    def walk(self, visitor):
        pass

    def pos(self):
        return self.token.position

    def end(self):
        return self.token.position + self.token.length

@dataclass(slots=True, repr=True)
class Literal(Node):
    token: Token

    @walk_func
    def walk(self, visitor):
        pass

    def pos(self):
        return self.token.position

    def end(self):
        return self.token.position + self.token.length

@dataclass(slots=True, repr=True)
class CallExpr(Node):
    func: Node 
    left_paren: Token
    args: list
    right_paren: Token
    
    @walk_func
    def walk(self, visitor):
        for arg in args: arg.val.walk(visitor)

    def pos(self): return self.func.pos()

    def end(self): return self.right_paren.pos + 1 # len(')')

@dataclass(slots=True, repr=True)
class PostfixExpr(Node):
    expr: Node
    op: Token
    
    @walk_func
    def walk(self, visitor):
        if self.val is not None: self.val.walk(visitor)

    def pos(self): return self.expr.pos()

    def end(self): return self.expr.end() + op.length


@dataclass(slots=True, repr=True)
class UnaryExpr(Node):
    op: Token
    expr: Node

    @walk_func
    def walk(self, visitor):
        if self.expr is not None: self.expr.walk(visitor)

    def pos(self): return self.op.pos

    def end(self): return self.expr.end()

@dataclass(slots=True, repr=True)
class BinaryExpr(Node):
    op: Token
    lhs: Node
    rhs: Node
    
    @walk_func
    def walk(self, visitor):
        if self.lhs is not None: self.lhs.walk(visitor)
        if self.rhs is not None: self.rhs.walk(visitor)

    def pos(self): return self.lhs.pos

    def end(self): return self.rhs.end()

@dataclass(slots=True, repr=True)
class FuncType(Node):
    left_paren: Token
    args: list
    right_paren: Token
    arrow: Token
    ret: Node

    @walk_func
    def walk(self, visitor):
        for arg in self.args: visitor.visit(arg)
        
        visitor.visitor(self.ret)

    def pos(self): return self.left_paren.pos

    def end(self): return self.ret.end()

@dataclass(slots=True, repr=True)
class ReturnStmt(Node):
    ret: Token
    expr: Node | None

    @walk_func
    def walk(self, visitor):
        if self.expr is not None: self.expr.walk(visitor)

    def pos(self): return self.ret.pos

    def end(self): return self.expr.end()

@dataclass(slots=True, repr=True)
class Declaration(Node):
    name: Token
    type_expr: Node
    expr: Node | None = None

    @walk_func
    def walk(self, visitor):
        if self.type_expr is not None: self.type_expr.walk(visitor)
        if self.expr is not None: self.expr.walk(visitor)

    def pos(self): return self.name.pos

    def end(self): return self.expr.end()

@dataclass(slots=True, repr=True)
class CodeBlock(Node):
    left_curly: Token
    statements: list
    right_curly: Token
    
    @walk_func
    def walk(self, visitor):
        for stmt in self.statements: visitor.visit(self)

    def pos(self): return self.left_curly.pos

    def end(self): return self.right_curly.pos + 1 # len('{')

@dataclass(slots=True, repr=True)
class Module(Node):
    name: Token 
    statements: list
    
    @walk_func
    def walk(self, visitor):
        for stmt in self.statements: visitor.visit(self)

    def pos(self): return self.name.pos

    def end(self): return self.statements[-1].end()

