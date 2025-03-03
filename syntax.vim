if exists("b:current_syntax")
    finish
endif

syn clear

syn keyword mylangTodo contained TODO FIXME XXX
syn region mylangComment start=/#/ end=/$/ contains=mylangTodo

syn match mylangMacro display /\$[A-Za-z_][A-Za-z0-9_]*/

syn keyword mylangStatement return module
syn keyword mylangImport import from as
syn keyword mylangStructure enum union struct

syn keyword mylangType i8 i16 i32 i64
syn keyword mylangType u8 u16 u32 u64
syn keyword mylangType f16 f32 f64
syn keyword mylangType int uint bool type

syn keyword mylangConstant null true false

syn match mylangSpecial display contained "\\\%(x\x\+\|.\|$\)"
syn region mylangString start=/\"/ end=/\"/ skip=/\\\\\|\\/ contains=mylangSpecial excludenl extend
syn region mylangChar start=/'/ end=/'/ skip=/\\\\\|\\/ contains=mylangSpecial excludenl extend

syn match mylangNumber  "\<\d*\>" display
syn match mylangHex     "\<0x\x\+\>" display
syn match mylangFloat   "\<\d\%(\d*\)\=\.\d*\>" display
syn match mylangFloat   "\<\d\%(\d*\)\=\.\d*e\d\+\d\>" display

hi def link mylangTodo      Todo
hi def link mylangComment   Comment

hi def link mylangMacro     Function

hi def link mylangStatement Statement
hi def link mylangImport    Include
hi def link mylangStructure Structure
hi def link mylangType      Type
hi def link mylangConstant  Constant

hi def link mylangSpecial   SpecialChar
hi def link mylangString    String
hi def link mylangChar      Character

hi def link mylangNumber    Number
hi def link mylangFloat     Number
hi def link mylangHex       Number

