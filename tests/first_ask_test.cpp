// SPDX-License-Identifier: GPL-3.0-or-later
// gpu/vk/first_ask.h alone (tests/test_first_ask.py)
#include "../gpu/vk/first_ask.h"
#include <cstdio>
#include <cstdlib>
#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "CHECK failed line %d: %s\n", __LINE__, #c); std::exit(1); } } while (0)

int main() {
    using first_ask::Budget;
    {   // asks of the usual cost: as many as the count allows, in every frame anew
        Budget b;
        int n = 0;
        while (b.allow(7)) b.spent(0.1), n++;
        CHECK(n == first_ask::kAsksAFrame && !b.allow(7));
        CHECK(b.allow(8));   // (the next frame)
        b.spent(0.1);
        CHECK(b.asks == 1 && b.frame == 8);
    }
    {   // slow asks: none begins once the frame's time is spent; the one that ran over is the last
        Budget b;
        CHECK(b.allow(1));
        b.spent(1.2);
        CHECK(b.allow(1));
        b.spent(1.2);
        CHECK(b.allow(1));
        b.spent(5.0);   // (a 99th-percentile ask: over the budget by itself)
        CHECK(!b.allow(1) && b.asks == 3 && b.ms > first_ask::kBudgetMs);
        CHECK(b.ms <= first_ask::kBudgetMs + 5.0);   // (the frame's worst: the budget and one ask)
        CHECK(b.allow(2) && b.asks == 0 && b.ms == 0);
    }
    {   // one very slow ask ends the frame's asks; a clock that went backwards costs nothing and still counts
        Budget b;
        CHECK(b.allow(3));
        b.spent(40.0);
        CHECK(!b.allow(3));
        Budget c;
        CHECK(c.allow(3));
        c.spent(-1.0);
        CHECK(c.asks == 1 && c.ms == 0 && c.allow(3));
    }
    CHECK(first_ask::kAsksAFrame >= 8 && first_ask::kBudgetMs > 0 && first_ask::kBudgetMs <= 4.0);   // (a quarter of a 60 Hz frame at most)
    std::printf("first_ask: ok\n");
    return 0;
}
