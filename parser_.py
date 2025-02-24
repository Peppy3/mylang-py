from tokens import Token, TokenEnum
from parser_file import ParserFile
from lexer import Lexer

import ast_ as ast

PARSER_DEBUG: bool = False

def parser_func(func):
	if PARSER_DEBUG:
		def f(*args):
			print(f"START: {func.__name__}")
			ret = func(*args)
			print(f"END: {func.__name__}")
			return ret
		return f
	return func

class Parser:
	def __init__(self, filename, src):
		self.filename = filename
		self.src = src
		self.errors = 0

		self.lexer = Lexer(self.src)

		self.current = self.lexer.next()
		self.lookahead = self.lexer.next()

	def _error(self, msg):
		self.errors += 1

		line_pos, col_pos = self.src.get_tok_human_pos(self.current)
		line_str = self.src.get_line(self.current)
		
		print(f"{self.filename}: {line_pos}:{col_pos} {msg}")
		if line_str is None:
			print("EOF")
			return

		print(line_str)
		for i in range(col_pos - 1):
			if line_str[i] == '\t':
				print("\t", end="")
			else:
				print(" ", end="")
		print("^")

	def next(self):
		tok = self.current
		self.current = self.lookahead
		self.lookahead = self.lexer.next()
		return tok

	def expect(self, typ):
		if self.current.type != typ:
			self._error(f"Expected {typ.name} but got {self.current.type.name}")
			return None
		else:
			return self.next()

	@parser_func
	def primary_expr(self):
		if self.current.type == TokenEnum.Identifier:
			return ast.Literal(self.next())
		if self.current.type == TokenEnum.IntegerLiteral:
			return ast.Literal(self.next())
		elif self.current.type == TokenEnum.IntegerLiteral:
			return ast.Literal(self.next())
		elif self.current.type == TokenEnum.HexLiteral:
			return ast.Literal(self.next())
		elif self.current.type == TokenEnum.FloatLiteral:
			return ast.Literal(self.next())
		elif self.current.type == TokenEnum.CharLiteral:
			return ast.Literal(self.next())
		elif self.current.type == TokenEnum.StringLiteral:
			return ast.Literal(self.next())
		elif self.current.type == TokenEnum.LeftParen:
			self.expect(TokenEnum.LeftParen)
			expr = self.expression()
			self.expect(TokenEnum.RightParen)
			return expr
		else:
			self._error(f"Expected literal or expression but got {self.current.type.name}")
			return None

	@parser_func
	def argument_expression_list(self):
		args = list()

		while True:
			args.append(self.expression())

			if self.current.type == TokenEnum.RightParen:
				break

			self.expect(TokenEnum.Comma)

		return args
	
	@parser_func
	def postfix_expression(self, primary=None):
		if primary is None:
			primary = self.primary_expr()

		if self.current.type == TokenEnum.Increment:
			return ast.PostfixExpr(self.next(), primary)
		elif self.current.type == TokenEnum.Decrement:
			return ast.PostfixExpr(self.next(), primary)
		elif self.current.type == TokenEnum.LeftParen:
			self.next()
			args = self.argument_expression_list()
			self.expect(TokenEnum.RightParen)
			return ast.CallExpr(primary, args)
		else:
			return primary

	@parser_func
	def unary_expression(self):
		if self.current.is_unary():
			op = self.next()
			return ast.UnaryExpr(op, self.unary_expression())
		else:
			return self.postfix_expression()

	@parser_func
	def binary_expression(self, lhs=None, min_precedence=0):
		if lhs is None:
			lhs = self.unary_expression()

		while True:
			op_prec = self.current.precedence()

			if op_prec < 1:
				return lhs

			op = self.next()
			rhs = self.binary_expression(None, op_prec + 1)
			
			tmp = ast.BinaryExpr(op, lhs, rhs)
			lhs = tmp

	type_expression = binary_expression
	
	@parser_func
	def assignment_expression(self):
		lhs = self.binary_expression()

		if TokenEnum.ASSIGNMENT_START > self.current.type or self.current.type > TokenEnum.ASSIGNMENT_END:
			return lhs

		op = self.next()
		rhs = self.binary_expression()
		return ast.BinaryExpr(op, lhs, rhs)

	expression = assignment_expression

	@parser_func
	def expression_statement(self):
		expr = self.expression()
		self.expect(TokenEnum.Semicolon)
		return expr

	@parser_func
	def function_type(self):
		# (x: int, y:int) ->int
		self.expect(TokenEnum.LeftParen)
		args = self.declaration_list()
		self.expect(TokenEnum.RightParen)
		self.expect(TokenEnum.Arrow)
		ret = self.type_expression()
		return ast.FuncType(args, ret)
		
	@parser_func
	def declaration_list(self):
		decls = list()
		while True:
			if self.current.type == TokenEnum.RightParen:
				return decls
			
			decls.append(self.declaration())

			if self.current.type != TokenEnum.Comma:
				return decls
			self.next()

	
	@parser_func
	def declaration(self):
		name = self.expect(TokenEnum.Identifier)
		self.expect(TokenEnum.Colon)
		
		type_expr = None
		if self.current.type == TokenEnum.LeftParen:
			type_expr = self.function_type()
		else:
			type_expr = self.type_expression()

		return ast.Declaration(name, type_expr, None)

	@parser_func
	def declaration_statement(self):
		decl = self.declaration()

		if self.current.type == TokenEnum.Assignment:
			self.next()
			decl.expr = self.expression_statement()
		elif self.current.type == TokenEnum.LeftCurly:
			decl.expr = self.compound_statement()
		else:
			self.expect(TokenEnum.Semicolon)

		return decl

	@parser_func
	def statement(self):
		if self.current.type == TokenEnum.Identifier and self.lookahead.type == TokenEnum.Colon:
			return self.declaration_statement()
		else:
			return self.expression_statement()

	@parser_func
	def statement_list(self):
		statements = list()
		while self.current.type != TokenEnum.RightCurly and self.current.type != TokenEnum.Eof:
			statements.append(self.statement())

		return statements

	@parser_func
	def compound_statement(self):
		self.expect(TokenEnum.LeftCurly)
		statements = self.statement_list()
		self.expect(TokenEnum.RightCurly)
		return statements

	@parser_func
	def module(self):

		module = self.expect(TokenEnum.Module)
		if module is None: return None

		name = self.expect(TokenEnum.Identifier)
		if name is None: return None

		semi = self.expect(TokenEnum.Semicolon)
		if semi is None: return None

		statements = None
		if self.current.type == TokenEnum.Eof:
			statements = [ast.Literal(self.next())]
		else:
			statements = self.statement_list()

		return ast.Module(name, statements)

def parse(filename, src):
	parser = Parser(filename, src)
	ast = parser.module()

	return parser.errors, ast

