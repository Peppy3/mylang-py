if exists("b:current_syntax")
    finish
endif

syn clear

syn region mylangComment start=/#/ end=/$/
syn keyword mylangStatement return module
syn keyword mylangImport import from as
syn keyword mylangStructure enum union struct

syn keyword mylangType i8 i16 i32 i64
syn keyword mylangType u8 u16 u32 u64
syn keyword mylangType f16 f32 f64

syn region mylangString start=/\"/ end=/\"/

hi def link mylangStatement Statement
hi def link mylangImport Include
hi def link mylangStructure Structure
hi def link mylangType Type
hi def link mylangComment Comment
hi def link mylangString String


