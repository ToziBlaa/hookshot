"""Live final stereo mixing: safe averages, Off identity, and unchanged surround.

Compile the real mixer helper, and check its live option, menu row and default.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

RUN_ALL_ARGS = ["--cc", "gcc"]
ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc", default="gcc")
    args = parser.parse_args()
    source = read("host/nn_audio.c")
    start = source.index("static void audio_mono(")
    function = source[start:source.index("\n}", start) + 2]
    fixture = r"""
#include <stdint.h>
#include <assert.h>
#include <string.h>
FUNCTION
int main(void) {
    const int16_t original[] = {32767,32767,-32768,-32768,32767,-32768,0,2000,-3000,1000,0,0};
    const int16_t expected[] = {32767,32767,-32768,-32768,0,0,1000,1000,-1000,-1000,0,0};
    int16_t pcm[12];
    memcpy(pcm, original, sizeof pcm);
    audio_mono(pcm, 6, 2, 0);
    assert(memcmp(pcm, original, sizeof pcm) == 0);
    audio_mono(pcm, 6, 2, 1);
    assert(memcmp(pcm, expected, sizeof pcm) == 0);
    /* Turning Off on the next frame restores stereo, without a restart. */
    memcpy(pcm, original, sizeof pcm);
    audio_mono(pcm, 6, 2, 0);
    assert(memcmp(pcm, original, sizeof pcm) == 0);
    audio_mono(pcm, 2, 6, 1);
    assert(memcmp(pcm, original, sizeof pcm) == 0);
    audio_mono(pcm, 0, 2, 1);
    assert(memcmp(pcm, original, sizeof pcm) == 0);
}
""".replace("FUNCTION", function)
    loop = source[source.index("static DWORD WINAPI renderer_main"):]
    mix = loop.index("audio_mono(pcm, FRAME, out_channels, rx_option(HOS_OPT_MONO_AUDIO, 0))")
    assert loop.index("audio_apply_gain(pcm") < mix < loop.index("output_frame(pcm)")
    assert "if (id == HOS_OPT_MONO_AUDIO) return opts.mono_audio;" in read("gpu/vk/vk_replay.cpp")
    assert re.search(r"int mono_audio\s*=\s*0;", read("gpu/vk/vk_menu.h"))
    assert re.search(
        r'\{TAB_AUDIO, "Mono audio", &opts.mono_audio, 0, 1, 1, tx_onoff,\s*'
        r'"[^"]+", nullptr, false, true\}', read("gpu/vk/vk_menu.cpp"))
    # Main has assigned the fork's original id 46 to Button prompts.
    ids = re.findall(r"(HOS_OPT_\w+)\s*=\s*(\d+)", read("gpu/vk/vk_api.h"))
    mono_id = dict(ids)["HOS_OPT_MONO_AUDIO"]
    assert [name for name, value in ids if value == mono_id] == ["HOS_OPT_MONO_AUDIO"]
    with tempfile.TemporaryDirectory() as directory:
        c = Path(directory) / "mono.c"
        c.write_text(fixture, encoding="utf-8")
        exe = Path(directory) / ("mono.exe" if os.name == "nt" else "mono")
        subprocess.run([args.cc, "-Wall", "-Wextra", "-Werror", str(c), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print("PASS: live mono, extremes, silence, Off identity, surround unchanged, menu wiring and default")


if __name__ == "__main__":
    main()
