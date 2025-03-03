if exists("b:current_syntax")
    finish
endif

syn clear

syn keyword mylangTodo contained TODO FIXME XXX

syn region mylangComment start=/#/ end=/$/ contains=mylangTodo

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

hi def link mylangTodo Todo
hi def link mylangComment Comment

hi def link mylangStatement Statement
hi def link mylangImport Include
hi def link mylangStructure Structure
hi def link mylangType Type
hi def link mylangConstant Constant

hi def link mylangSpecial SpecialChar
hi def link mylangString String
hi def link mylangChar Character

