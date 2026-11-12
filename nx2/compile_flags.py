"""The CPU flags a build compiled with, recorded beside the game and in the binary.

hookshot_flags.txt in the game folder is that line. hos_main.c prints the same text
(HOOKSHOT_COMPILE_FLAGS, given to that file only) so the log says what produced the binary.
Issue 2576.

-march and -ffp-contract=off are always there. -mtune is there when this PC or RX_MTUNE
set one. RX_CPU_FLAGS adds further machine flags after those, and only those: a token
has to start with -m (for example -mprefer-vector-width=256). Anything else is left
out, including -ffast-math and -Ofast, because the lifted code is proved with
contraction off and the rounding written in the source.

make_game.py copies the "compile flags:" line build.py prints. It does not ask this
process for the list again.
"""
import os
import re


def cpu_flags(march, mtune, extra):
    """The CPU flags for this build, in the order clang receives them."""
    flags = ["-march=" + march, "-ffp-contract=off"]
    if mtune:
        flags.append("-mtune=" + mtune)
    for part in (extra or "").split():
        if part.startswith("-m"):   # (machine flags only: -ffast-math and -Ofast would change the rounding)
            flags.append(part)
    return flags


def text(flags):
    """One line, safe as a C string and as the flags= value."""
    return re.sub(r"[^A-Za-z0-9 ._+=,/:-]", "_", " ".join(flags))


def define(flags):
    return '-DHOOKSHOT_COMPILE_FLAGS="%s"' % text(flags)


def from_build_line(line):
    """The flag list from the line build.py prints, or None when the line is something else."""
    prefix = "compile flags: "
    if not line.startswith(prefix):
        return None
    return line[len(prefix):].split()


def current():
    """The flags this process would compile with (RX_MARCH, RX_MTUNE, RX_CPU_FLAGS, else this PC)."""
    from host_cpu import host_march, host_mtune
    march = os.environ.get("RX_MARCH") or host_march()
    mtune = os.environ.get("RX_MTUNE") or host_mtune()
    return cpu_flags(march, mtune, os.environ.get("RX_CPU_FLAGS", ""))


def write(folder, flags):
    """hookshot_flags.txt from the list the compile used. The version file beside it is left as it is."""
    path = os.path.join(folder, "hookshot_flags.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("flags=%s\n" % text(flags))
    return path
