#include "global.h"
#include "pokemon_storage_system.h"
#include "xgba_e6.h"

// 20 worlds, two 0x44000-byte copies per world, eight native PC pages each.
// CPU 0x0F360000 corresponds to save file 0x380000. Backups end at 0xE20000.
// The emulator's separate E6 header backup begins at file offset 0xFFF000.
#define XGBA_E6_BOX_BASE ((volatile u8 *)0x0F360000)
#define XGBA_E6_BOX_SLOT_SIZE 0x44000
#define XGBA_E6_BOX_HEADER_SIZE 36
#define XGBA_E6_BOX_PAGES 8
#define XGBA_E6_BOX_VERSION 1
#define XGBA_E6_BOX_DATA_SIZE (XGBA_E6_BOX_PAGES * sizeof(struct PokemonStorage))

typedef char XgbaE6BoxesFit[(XGBA_E6_BOX_HEADER_SIZE + XGBA_E6_BOX_DATA_SIZE
    <= XGBA_E6_BOX_SLOT_SIZE) ? 1 : -1];

static const u8 sBoxMagic[8] = {'X','G','B','A','E','6','B',0};
static u8 sCurrentWorld;
static u8 sCurrentPage;

static u16 Read16(const volatile u8 *p)
{
    return p[0] | ((u16)p[1] << 8);
}

static u32 Read32(const volatile u8 *p)
{
    return (u32)p[0] | ((u32)p[1] << 8)
        | ((u32)p[2] << 16) | ((u32)p[3] << 24);
}

static void Write16(volatile u8 *p, u16 n)
{
    p[0] = n;
    p[1] = n >> 8;
}

static void Write32(volatile u8 *p, u32 n)
{
    p[0] = n;
    p[1] = n >> 8;
    p[2] = n >> 16;
    p[3] = n >> 24;
}

static u32 UpdateCrc(u32 crc, u8 value)
{
    u32 i;

    crc ^= value;
    for (i = 0; i < 8; i++)
    {
        if (crc & 1)
            crc = (crc >> 1) ^ 0xEDB88320;
        else
            crc >>= 1;
    }
    return crc;
}

static u32 Checksum(const volatile u8 *bytes, u32 size)
{
    u32 crc = 0xFFFFFFFF;
    u32 i;

    for (i = 0; i < size; i++)
        crc = UpdateCrc(crc, bytes[i]);
    return crc ^ 0xFFFFFFFF;
}

static volatile u8 *GetSlot(u8 world, u8 slot)
{
    return XGBA_E6_BOX_BASE + ((world - 1) * 2 + slot) * XGBA_E6_BOX_SLOT_SIZE;
}

// 1 = valid, 0 = unused, -1 = corrupt.
static s8 InspectSlot(u8 world, u8 slot, u32 *sequence, u8 *page, u8 *mask)
{
    const volatile u8 *p = GetSlot(world, slot);
    u32 i;

    if (p[0] == 0xFF)
        return 0;
    for (i = 0; i < sizeof(sBoxMagic); i++)
    {
        if (p[i] != sBoxMagic[i])
            return -1;
    }
    if (Read16(p + 8) != XGBA_E6_BOX_VERSION || Read16(p + 10) != world)
        return -1;
    *sequence = Read32(p + 12);
    *page = Read32(p + 16);
    *mask = Read32(p + 20);
    if (!*sequence || *page >= XGBA_E6_BOX_PAGES
        || Read32(p + 24) != XGBA_E6_BOX_DATA_SIZE
        || ((*mask & (1 << *page)) == 0)
        || (*mask > 0xFF)
        || Read32(p + 32) != Checksum(p, 32))
        return -1;
    if (Read32(p + 28) != Checksum(p + XGBA_E6_BOX_HEADER_SIZE, XGBA_E6_BOX_DATA_SIZE))
        return -1;
    return 1;
}

static s8 FindLatest(u8 world, u8 *slot, u32 *sequence, u8 *page, u8 *mask)
{
    u32 seq0 = 0, seq1 = 0;
    u8 page0 = 0, page1 = 0, mask0 = 0, mask1 = 0;
    s8 a = InspectSlot(world, 0, &seq0, &page0, &mask0);
    s8 b = InspectSlot(world, 1, &seq1, &page1, &mask1);

    if (a == 1 && (b != 1 || seq0 >= seq1))
    {
        *slot = 0;
        *sequence = seq0;
        *page = page0;
        *mask = mask0;
        return 1;
    }
    if (b == 1)
    {
        *slot = 1;
        *sequence = seq1;
        *page = page1;
        *mask = mask1;
        return 1;
    }
    if (a < 0 || b < 0)
        return -1;
    *slot = 1;
    *sequence = 0;
    *page = 0;
    *mask = 0;
    return 0;
}

// Write the entire new bank to the inactive copy first, then publish its magic.
// This preserves the previous complete bank if interrupted partway through.
static bool8 CommitBank(u8 world, u8 targetPage)
{
    u8 currentSlot, activePage, mask;
    u32 sequence;
    u32 page, i, crc;
    s8 state;
    const volatile u8 *oldData = NULL;
    volatile u8 *dest;
    u8 *live = (u8 *)gPokemonStoragePtr;

    if (!XgbaE6Available() || world < 1 || world > 20
        || targetPage >= XGBA_E6_BOX_PAGES)
        return FALSE;
    state = FindLatest(world, &currentSlot, &sequence, &activePage, &mask);
    if (state < 0 || sequence == 0xFFFFFFFF)
        return FALSE;
    if (state == 1)
        oldData = GetSlot(world, currentSlot) + XGBA_E6_BOX_HEADER_SIZE;
    else
        activePage = 0;

    dest = GetSlot(world, state == 1 ? 1 - currentSlot : 0);
    // Invalidate target copy before writing. Never touch the good copy.
    for (i = 0; i < sizeof(sBoxMagic); i++)
        dest[i] = 0xFF;
    crc = 0xFFFFFFFF;
    for (page = 0; page < XGBA_E6_BOX_PAGES; page++)
    {
        for (i = 0; i < sizeof(struct PokemonStorage); i++)
        {
            u8 value;
            if (page == sCurrentPage)
                value = live[i];
            else if (oldData != NULL && (mask & (1 << page)))
                value = oldData[page * sizeof(struct PokemonStorage) + i];
            else
                value = 0;
            dest[XGBA_E6_BOX_HEADER_SIZE + page * sizeof(struct PokemonStorage) + i] = value;
            crc = UpdateCrc(crc, value);
        }
    }
    // The current RAM page is authoritative for that page alone. The other
    // seven pages always come from the last valid bank, never from live RAM.
    mask |= (1 << sCurrentPage);
    if (targetPage != sCurrentPage)
        return FALSE;
    Write16(dest + 8, XGBA_E6_BOX_VERSION);
    Write16(dest + 10, world);
    Write32(dest + 12, sequence + 1);
    Write32(dest + 16, targetPage);
    Write32(dest + 20, mask);
    Write32(dest + 24, XGBA_E6_BOX_DATA_SIZE);
    Write32(dest + 28, crc ^ 0xFFFFFFFF);

    // Header CRC covers magic, so publish magic before its CRC last.
    for (i = 0; i < sizeof(sBoxMagic); i++)
        dest[i] = sBoxMagic[i];
    Write32(dest + 32, Checksum(dest, 32));
    return TRUE;
}

// If world has no page bank yet, page 1 is initialized from its existing
// saved native PC. All other pages are created on demand.
bool8 XgbaE6BoxesEnterWorld(u8 world)
{
    u8 slot, page, mask;
    u32 seq, i;
    s8 state;
    const volatile u8 *data;
    u8 *live = (u8 *)gPokemonStoragePtr;

    if (!XgbaE6Available() || world < 1 || world > 20)
        return FALSE;
    state = FindLatest(world, &slot, &seq, &page, &mask);
    if (state < 0)
        return FALSE;
    if (state == 0)
    {
        sCurrentWorld = world;
        sCurrentPage = 0;
        return CommitBank(world, 0);
    }
    data = GetSlot(world, slot) + XGBA_E6_BOX_HEADER_SIZE
        + page * sizeof(struct PokemonStorage);
    for (i = 0; i < sizeof(struct PokemonStorage); i++)
        live[i] = data[i];
    sCurrentWorld = world;
    sCurrentPage = page;
    return TRUE;
}

static bool8 EnsureWorld(u8 world)
{
    if (world == sCurrentWorld)
        return TRUE;
    return XgbaE6BoxesEnterWorld(world);
}

bool8 XgbaE6BoxesCheckpoint(u8 world)
{
    if (!EnsureWorld(world))
        return FALSE;
    return CommitBank(world, sCurrentPage);
}

u8 XgbaE6BoxesGetPage(u8 world)
{
    if (!EnsureWorld(world))
        return 0;
    return sCurrentPage;
}

bool8 XgbaE6BoxesSwitchPage(u8 world, u8 nextPage)
{
    u8 slot, page, mask;
    u32 seq, i;
    s8 state;
    const volatile u8 *source;
    u8 *live = (u8 *)gPokemonStoragePtr;

    if (nextPage >= XGBA_E6_BOX_PAGES || !EnsureWorld(world))
        return FALSE;
    if (nextPage == sCurrentPage)
        return TRUE;

    // Save the old resident page without touching the previous backup.
    if (!CommitBank(world, sCurrentPage))
        return FALSE;
    state = FindLatest(world, &slot, &seq, &page, &mask);
    if (state != 1)
        return FALSE;

    if (mask & (1 << nextPage))
    {
        source = GetSlot(world, slot) + XGBA_E6_BOX_HEADER_SIZE
            + nextPage * sizeof(struct PokemonStorage);
        for (i = 0; i < sizeof(struct PokemonStorage); i++)
            live[i] = source[i];
    }
    else
    {
        ResetPokemonStorageSystem();
    }
    sCurrentPage = nextPage;
    // Now the new page is resident. Publish its initialized contents.
    return CommitBank(world, nextPage);
}
