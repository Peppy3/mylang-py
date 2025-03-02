import sys
import platform

from importlib import import_module
    
# Every asm generator lives in it's own sub-module which is imported dynamically
# They should have have a generate(src, ast) -> io.StringIO | None function which gets called
# to generate assembly for the target (None here means there was some kind of error)

# map from os-arch to ..os_arch (search path for importlib.import_module())
# (..os_arch is the relative path to the module)
ASM_ARCH: dict = {
    "foo-arch": "..foo_arch",
    "linux-aarch64": "..linux_aarch64",
}

def list_targets():
    targets = ASM_ARCH.keys()
    print("\n".join(reversed(targets)))

def gen_asm(src, ast, target: str | None):
    
    if target is None:
        target = f"{sys.platform}-{platform.machine()}"

    asm_generator = ASM_ARCH.get(target)
    if asm_generator is None:
        print(f"No assembly generator for {target}")
        return None
    
    generator_module = import_module(asm_generator, "asm_gen.__init__")

    out = generator_module.generate(src, ast)
    
    


