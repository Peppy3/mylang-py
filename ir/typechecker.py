import ir.core as ir

def get_type(rep, val):
    if isinstance(val, ir.Constant):
        return val.type
    else:
        val = rep.lookup(val)
        return val

def typecheck(src, rep, num_errors=0):

    for instr in rep.instr_list:
        if instr.op == ir.OpEnum.MUL:
            lhs = get_type(rep, instr.args[1])
            rhs = get_type(rep, instr.args[2])

            if lhs is None or rhs is None:
                continue

            if lhs != rhs:
                num_errors += 1
                continue

            ret = rep.lookup(instr.args[0])
            ret.type = lhs

        elif instr.op == ir.OpEnum.ADD:
            lhs = get_type(rep, instr.args[1])
            rhs = get_type(rep, instr.args[2])

            if lhs is None or rhs is None:
                continue

            if lhs != rhs:
                num_errors += 1
                continue

            ret = rep.lookup(instr.args[0])
            ret.type = lhs
        elif instr.op == ir.OpEnum.MOVE:
            lhs = get_type(rep, instr.args[0])
            rhs = get_type(rep, instr.args[1])
            print(lhs, rhs)
        else:
            raise NotImplementedError(instr.op.name)
    
    return num_errors

