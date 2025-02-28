from pprint import pprint

class EnumType:
    __slots__ = "val", "name" 
    def __init__(self, val, name=None):
        self.val = val
        self.name = name

    __repr__ = lambda self: f"EnumToken({self.val}, {self.name})"

    __eq__ = lambda self, other: self.val == other.val
    __lt__ = lambda self, other: self.val < other.val
    __gt__ = lambda self, other: self.val > other.val

auto_idx: int = 0

def auto(reset=False):
    global auto_idx
    if reset:
        auto_idx = 0
    else:
        auto_idx += 1
    return EnumType(auto_idx)

def enum(cls):
    global auto_idx
    auto_idx = 0

    for k, v in cls.__dict__.items():
        if isinstance(v, EnumType):
            #print(k, v)
            v.name = k

    pprint(cls.__dict__)

    return cls

