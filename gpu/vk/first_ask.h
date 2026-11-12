// SPDX-License-Identifier: GPL-3.0-or-later
// (hookshot) A draw whose pipeline no list named (a state first seen in play) used to be left out while a worker made the
// pipeline, even where the driver's cache had it and answered in a fraction of a millisecond: a new game's opening drew 834
// such pipelines, all from the driver's cache, none compiled, and still left 1,906 draws out. Now the draw first asks the
// caches itself, without compiling, and goes on with the pipeline when they answer; only one that needs compiling goes to
// the worker and is left out, as before. This is how much of a frame those asks may take, on each recording thread: an ask
// is about 0.2 ms (median; 99 in 100 under 5 ms on an RTX 3090), so a burst of new states at an area's first frames is
// served over a few frames instead of costing one long one. Nothing of Vulkan here: tests/test_first_ask.py.
#pragma once
#include <cstdint>

namespace first_ask {

constexpr int kAsksAFrame = 24;     // (asks begun in one frame)
constexpr double kBudgetMs = 3.0;   // (their time in one frame: no ask begins once it is spent; the last may run over it)

struct Budget {
    uint64_t frame = ~0ull;
    int asks = 0;
    double ms = 0;
    /// Whether one more ask may begin in this frame
    bool allow(uint64_t now_frame) {
        if (now_frame != frame) frame = now_frame, asks = 0, ms = 0;
        return asks < kAsksAFrame && ms < kBudgetMs;
    }
    /// An ask that began took this long
    void spent(double took_ms) {
        asks++;
        ms += took_ms > 0 ? took_ms : 0;
    }
};

}   // namespace first_ask
