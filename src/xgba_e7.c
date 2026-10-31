#include "global.h"
#include "event_data.h"
#include "xgba_e7_data.h"

// Actual emulated CPU reads at 0x10xxxxxx-0x1FFFFFFF. No save writes,
// full-ROM scans, 256 MiB heap allocations, or additional GBA RAM.
void XgbaE7SpecialProbe(void)
{
    u32 i;
    u32 j;

    gSpecialVar_Result = 0;
    for (i = 0; i < XGBA_E7_PROBE_COUNT; i++)
    {
        const volatile u8 *rom =
            (const volatile u8 *)(0x10000000u + sXgbaE7ProbeOffsets[i]);

        for (j = 0; j < 16; j++)
        {
            if (rom[j] != sXgbaE7ProbeBytes[i][j])
                return;
        }
    }
    gSpecialVar_Result = 1;
}
