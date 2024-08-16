import subprocess
import json
from typing import Any, Dict, List, Optional, Tuple
import dataclasses
import random
import base64
from os import path
from queue import SimpleQueue
from copy import deepcopy
from sys import stderr, argv
import re


GLOBAL_LIBRARIES: List[str] = ["std"]

USE_REGEX = re.compile(r'(^|;|\n)[ \t]*(export +|)use +([^ ;\n\t]+)')


def main(main_nu_file: str = "test.nu") -> None:
    modules: Dict[str, NuModule] = {}

    # find and load all modules
    main_module = NuModule(path.abspath(main_nu_file))
    modules[path.abspath(main_nu_file)] = main_module
    load_q: SimpleQueue[str] = SimpleQueue()
    for i in main_module.uses:
        load_q.put(i)
    while not load_q.empty():
        mod_path: str = load_q.get()
        if mod_path in modules:
            continue
        mod: NuModule = NuModule(mod_path)
        modules[mod.filepath] = mod
        if path.basename(mod.filepath) == "mod.nu":
            modules[path.dirname(mod.filepath)] = mod
        for i in mod.uses:
            load_q.put(i)

    output: List[str] = []
    for mod in sort_modules(modules):
        if mod == main_module:  # manually at the end
            continue
        output.append(f"export module {mod.name} {{export module {mod.orig_name} {{ {mod.generate_mod(modules)} }} }}")
    output.append(main_module.generate_mod(modules))
    print("\n".join(output))


class NuModule:
    def __init__(self, filepath: str):
        if path.isdir(filepath):
            filepath = path.join(filepath, "mod.nu")
        self.filepath: str = filepath
        self.orig_name: str = (
            path.basename(filepath).split(".")[0]
            if path.basename(filepath) != "mod.nu"
            else path.basename(path.dirname(filepath))
        )
        stderr.write(f"DEBUG: found ORIGINAL_NAME: {self.orig_name}    FILEPATH: {filepath}\n")
        self.name: str = base64.b32encode(random.randbytes(32)).rstrip(b"=").decode("utf-8", errors="replace")
        self.uses: List[str] = []
        self.find_used_files()

    def generate_mod(self, modules: Dict[str, "NuModule"]) -> str:
        with open(self.filepath, "r") as fp:
            source_code: str = fp.read()

        def _rep(x: re.Match) -> str:
            mod: NuModule = modules[abspath(self.filepath, x[3])]
            target: str = f"{mod.name} {mod.orig_name}"
            return f"{x[1]}{x[2]}use {target}"

        return USE_REGEX.sub(_rep, source_code)

    def find_used_files(self) -> None:
        with open(self.filepath, "r") as fp:
            source_code: str = fp.read()
        self.uses = [abspath(self.filepath, i[2]) for i in USE_REGEX.findall(source_code)]


def sort_modules(modules: Dict[str, NuModule]) -> List[NuModule]:
    out: List[NuModule] = []
    todo: List[Tuple[str, List[str]]] = [(k, deepcopy(v.uses),) for k, v in modules.items()]
    last_len: int = len(todo)
    while last_len != 0:
        finished: List[str] = [i[0] for i in todo if len(i[1]) == 0]
        todo = [
            (i[0], [h for h in i[1] if h not in finished])
            for i in todo
            if i[0] not in finished
        ]
        for fm in finished:
            out.append(modules.get(fm))  # type: ignore
        assert last_len != len(todo), f"This script is currently unable to handle circular dependencies. Part of the problem: {', '.join(i[0] for i in todo)}"
        last_len = len(todo)
    return out


def abspath(file_path: str, mod_name: str) -> str:
    return path.abspath(
        path.join(
            path.dirname(file_path),
            # windows compatability (i hope)
            path.sep.join(f"{path.pardir}/".join(mod_name.split("../")).split("/")),
        )
    )


if __name__ == "__main__":
    main(argv[1])
