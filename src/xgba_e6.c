#include "global.h"
#include "load_save.h"
#include "event_data.h"
#include "pokemon_storage_system.h"
#include "xgba_e6.h"

#define XGBA_E6_BASE ((volatile u8 *)0x0F000000)
#define XGBA_E6_SLOT_SIZE 0x10000
#define XGBA_E6_PAYLOAD_CAPACITY (XGBA_E6_SLOT_SIZE - 32)
#define XGBA_E6_BANK_BASE 0xE0000
#define XGBA_E6_BACKUP_HEADER 0xFDF000

typedef char XgbaE6SnapshotFits[(sizeof(struct SaveBlock1) + sizeof(struct SaveBlock2)
    + sizeof(struct PokemonStorage) <= XGBA_E6_PAYLOAD_CAPACITY) ? 1 : -1];

static u8 XgbaE6CurrentWorld(void);

static const u8 sXgbaE6Superblock[24] = {
    'X', 'G', 'B', 'A', 'E', '6', 'S', 0,
    2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1,
    0xB0, 0x2B, 0x5B, 0x12
};

static const u8 sXgbaE6RecordMagic[8] = {
    'X', 'G', 'B', 'A', 'E', '6', 'W', 0
};

static u16 XgbaE6Read16(const volatile u8 *ptr)
{
    return (u16)ptr[0] | ((u16)ptr[1] << 8);
}

static u32 XgbaE6Read32(const volatile u8 *ptr)
{
    return (u32)ptr[0] | ((u32)ptr[1] << 8)
        | ((u32)ptr[2] << 16) | ((u32)ptr[3] << 24);
}

static void XgbaE6Write16(u8 *ptr, u16 value)
{
    ptr[0] = value;
    ptr[1] = value >> 8;
}

static void XgbaE6Write32(u8 *ptr, u32 value)
{
    ptr[0] = value;
    ptr[1] = value >> 8;
    ptr[2] = value >> 16;
    ptr[3] = value >> 24;
}

static u32 XgbaE6CrcStep(u32 crc, u8 value)
{
    return gXgbaE6CrcTable[(crc ^ value) & 0xFF] ^ (crc >> 8);
}

static u32 XgbaE6Crc(const volatile u8 *src, u32 count)
{
    u32 crc = 0xFFFFFFFF;
    u32 i;

    for (i = 0; i < count; i++)
        crc = XgbaE6CrcStep(crc, src[i]);
    return crc ^ 0xFFFFFFFF;
}

static bool8 XgbaE6HeaderValid(u32 offset)
{
    const volatile u8 *ptr = XGBA_E6_BASE + offset;
    u32 i;

    for (i = 0; i < sizeof(sXgbaE6Superblock); i++)
    {
        if (ptr[i] != sXgbaE6Superblock[i])
            return FALSE;
    }
    return TRUE;
}

bool8 XgbaE6Available(void)
{
    const volatile u8 *rom = (const volatile u8 *)0x08000000;
    const u8 tag[7] = { 'X', 'G', 'B', 'A', '2', '5', '6' };
    u32 i;

    if (rom[0xBC] != 0xE6)
        return FALSE;
    for (i = 0; i < sizeof(tag); i++)
    {
        if (rom[0xB5 + i] != tag[i])
            return FALSE;
    }
    return XgbaE6HeaderValid(0) || XgbaE6HeaderValid(XGBA_E6_BACKUP_HEADER);
}

static volatile u8 *XgbaE6Slot(u8 world, u8 slot)
{
    u32 offset = XGBA_E6_BANK_BASE + ((world - 1) * 2 + slot) * XGBA_E6_SLOT_SIZE;
    return XGBA_E6_BASE + offset;
}

static u32 XgbaE6SnapshotSize(void)
{
    return sizeof(struct SaveBlock1) + sizeof(struct SaveBlock2) + sizeof(struct PokemonStorage);
}

static u8 XgbaE6SnapshotByte(u32 index)
{
    if (index < sizeof(struct SaveBlock1))
        return ((const u8 *)gSaveBlock1Ptr)[index];
    index -= sizeof(struct SaveBlock1);

    if (index < sizeof(struct SaveBlock2))
        return ((const u8 *)gSaveBlock2Ptr)[index];
    index -= sizeof(struct SaveBlock2);

    return ((const u8 *)gPokemonStoragePtr)[index];
}

// 0 = unused, 1 = valid record, -1 = damaged record.
static s32 XgbaE6InspectSlot(u8 world, u8 slot, u32 *sequence, u32 *length)
{
    const volatile u8 *record = XgbaE6Slot(world, slot);
    u32 i;

    // Erased magic marks an unused/uncommitted slot. No 64 KiB scan.
    for (i = 0; i < sizeof(sXgbaE6RecordMagic); i++)
    {
        if (record[i] != 0xFF)
            break;
    }
    if (i == sizeof(sXgbaE6RecordMagic))
        return 0;

    for (i = 0; i < sizeof(sXgbaE6RecordMagic); i++)
    {
        if (record[i] != sXgbaE6RecordMagic[i])
            return -1;
    }
    if (XgbaE6Read16(record + 8) != 2 || XgbaE6Read16(record + 10) != world)
        return -1;

    *sequence = XgbaE6Read32(record + 12);
    *length = XgbaE6Read32(record + 16);
    if (*sequence == 0 || *length > XGBA_E6_PAYLOAD_CAPACITY
        || XgbaE6Read32(record + 28) != 0)
        return -1;

    if (XgbaE6Crc(record, 24) != XgbaE6Read32(record + 24))
        return -1;
    return 1;
}

static bool8 XgbaE6SlotPayloadValid(u8 world, u8 slot, u32 length)
{
    const volatile u8 *p = XgbaE6Slot(world, slot);
    return XgbaE6Crc(p + 32, length) == XgbaE6Read32(p + 20);
}

static s32 XgbaE6SelectWorld(u8 world, u8 *slot, u32 *sequence, u32 *length)
{
    u32 firstSeq = 0, secondSeq = 0, firstLen = 0, secondLen = 0;
    s32 first = XgbaE6InspectSlot(world, 0, &firstSeq, &firstLen);
    s32 second = XgbaE6InspectSlot(world, 1, &secondSeq, &secondLen);
    u8 preferred = second == 1 && (first != 1 || secondSeq > firstSeq) ? 1 : 0;

    // Check the newest payload first. The older A/B copy is a fallback,
    // not another full 53 KiB checksum on every ordinary access.
    if (preferred == 0 && first == 1
        && XgbaE6SlotPayloadValid(world, 0, firstLen))
    {
        *slot = 0;
        *sequence = firstSeq;
        *length = firstLen;
        return 1;
    }
    if (preferred == 1 && second == 1
        && XgbaE6SlotPayloadValid(world, 1, secondLen))
    {
        *slot = 1;
        *sequence = secondSeq;
        *length = secondLen;
        return 1;
    }
    if (preferred == 0 && second == 1
        && XgbaE6SlotPayloadValid(world, 1, secondLen))
    {
        *slot = 1;
        *sequence = secondSeq;
        *length = secondLen;
        return 1;
    }
    if (preferred == 1 && first == 1
        && XgbaE6SlotPayloadValid(world, 0, firstLen))
    {
        *slot = 0;
        *sequence = firstSeq;
        *length = firstLen;
        return 1;
    }
    if (first == 0 && second == 0)
    {
        *slot = 1;
        *sequence = 0;
        *length = 0;
        return 0;
    }
    return -1;
}

bool8 XgbaE6SnapshotWorld(u8 world)
{
    u8 slot;
    u8 header[32];
    u32 sequence;
    u32 oldLength;
    u32 length;
    u32 i;
    u32 crc;
    volatile u8 *record;
    s32 status;

    if (world < 1 || world > 20 || !XgbaE6Available())
        return FALSE;

    status = XgbaE6SelectWorld(world, &slot, &sequence, &oldLength);
    if (status < 0 || sequence == 0xFFFFFFFF)
        return FALSE;

    record = XgbaE6Slot(world, status == 1 ? 1 - slot : 0);
    length = XgbaE6SnapshotSize();

    // If the live save hasn't changed, avoid another 53 KiB extension write.
    crc = 0xFFFFFFFF;
    for (i = 0; i < length; i++)
        crc = XgbaE6CrcStep(crc, XgbaE6SnapshotByte(i));
    crc ^= 0xFFFFFFFF;
    if (status == 1 && oldLength == length
        && XgbaE6Read32(XgbaE6Slot(world, slot) + 20) == crc)
        return TRUE;

    for (i = 0; i < 32; i++)
        record[i] = 0xFF;
    for (i = 0; i < length; i++)
        record[32 + i] = XgbaE6SnapshotByte(i);

    // The remaining 64 KiB slot padding is outside the declared payload.
    memset(header, 0, sizeof(header));
    memcpy(header, sXgbaE6RecordMagic, sizeof(sXgbaE6RecordMagic));
    XgbaE6Write16(header + 8, 2);
    XgbaE6Write16(header + 10, world);
    XgbaE6Write32(header + 12, sequence + 1);
    XgbaE6Write32(header + 16, length);
    XgbaE6Write32(header + 20, crc);
    XgbaE6Write32(header + 24, XgbaE6Crc(header, 24));

    for (i = 8; i < sizeof(header); i++)
        record[i] = header[i];
    for (i = 0; i < sizeof(sXgbaE6RecordMagic); i++)
        record[i] = header[i];

    return TRUE;
}

// Called only when a map transition can rebuild navigation and map objects.
// The original 0x234 bytes (warps, camera and map view) remain from the lab;
// loading those from a different map here would poison the pending warp.
bool8 XgbaE6RestoreWorld(u8 world)
{
    u8 slot;
    u32 sequence;
    u32 length;
    u32 i;
    u16 chosenWorld;
    s32 status;
    const volatile u8 *source;
    u8 *save1 = (u8 *)gSaveBlock1Ptr;
    u8 *save2 = (u8 *)gSaveBlock2Ptr;
    u8 *storage = (u8 *)gPokemonStoragePtr;

    if (world < 1 || world > 20 || !XgbaE6Available())
        return FALSE;

    status = XgbaE6SelectWorld(world, &slot, &sequence, &length);
    if (status != 1 || length != XgbaE6SnapshotSize())
        return FALSE;

    source = XgbaE6Slot(world, slot) + 32;
    chosenWorld = gSaveBlock1Ptr->vars[VAR_XGBA_WORLD_ID - VARS_START];

    for (i = 0x234; i < sizeof(struct SaveBlock1); i++)
        save1[i] = source[i];
    for (i = 0; i < sizeof(struct SaveBlock2); i++)
        save2[i] = source[sizeof(struct SaveBlock1) + i];
    for (i = 0; i < sizeof(struct PokemonStorage); i++)
        storage[i] = source[sizeof(struct SaveBlock1) + sizeof(struct SaveBlock2) + i];

    gSaveBlock1Ptr->vars[VAR_XGBA_WORLD_ID - VARS_START] = chosenWorld;
    LoadPlayerParty();
    LoadPlayerBag();
    return XgbaE6BoxesEnterWorld(world);
}

static bool8 XgbaE6PrepareCurrentState(void)
{
    if (!XgbaE6Available())
        return FALSE;
    SavePlayerParty();
    SaveObjectEvents();
    // The live bag pockets already reside inside SaveBlock1. SavePlayerBag()
    // copies an outdated load-time cache back over the real item quantities.
    return TRUE;
}

void XgbaE6SpecialEnterWorld(void)
{
    u8 world;
    s32 status;
    s32 baseline;

    gSpecialVar_Result = 4;
    if (!XgbaE6Available())
    {
        gSpecialVar_Result = 0;
        return;
    }
    world = XgbaE6CurrentWorld();
    if (world < 2 || world > 20)
        return;

    // Reject a missing/legacy/corrupt destination PC before mutating live data.
    if (!XgbaE6BoxesCanEnterWorld(world))
        return;
    status = XgbaE6AuditWorld(world);
    if (status == 0)
    {
        baseline = XgbaE6AuditWorld(1);
        if (baseline == 0)
        {
            if (!XgbaE6PrepareCurrentState() || !XgbaE6SnapshotWorld(1))
                return;
        }
        else if (baseline < 0)
        {
            return;
        }
        if (!XgbaE6RestoreWorld(1))
            return;
        if (!XgbaE6PrepareCurrentState() || !XgbaE6SnapshotWorld(world))
            return;
        if (!XgbaE6BoxesEnterWorld(world))
            return;
    }
    else if (status < 0 || !XgbaE6RestoreWorld(world))
    {
        return;
    }
    gSpecialVar_Result = 1;
}

// Save original Hoenn before its resident state is replaced by a clone.
void XgbaE6SpecialLeaveWorldOne(void)
{
    gSpecialVar_Result = 4;
    if (XgbaE6CurrentWorld() != 1 || !XgbaE6Available())
        return;
    if (!XgbaE6PrepareCurrentState())
        return;
    if (!XgbaE6BoxesCheckpointNativeWorldOne())
        return;
    if (XgbaE6SnapshotWorld(1))
        gSpecialVar_Result = 1;
}

// Restore World 1 instead of reusing the previous clone's resident save.
void XgbaE6SpecialReturnToWorldOne(void)
{
    u8 previousWorld = XgbaE6CurrentWorld();

    gSpecialVar_Result = 4;
    if (!XgbaE6Available() || XgbaE6AuditWorld(1) != 1
        || !XgbaE6BoxesCanEnterWorld(1))
        return;
    if (!XgbaE6RestoreWorld(1))
    {
        if (previousWorld >= 2 && previousWorld <= 20)
            XgbaE6RestoreWorld(previousWorld);
        return;
    }
    VarSet(VAR_XGBA_WORLD_ID, 1);
    gSpecialVar_Result = 1;
}

void XgbaE6SpecialLeaveWorld(void)
{
    u8 world = XgbaE6CurrentWorld();

    gSpecialVar_Result = 4;
    if (!XgbaE6PrepareCurrentState())
    {
        gSpecialVar_Result = 0;
        return;
    }
    if (world >= 2 && world <= 20
        && XgbaE6BoxesCheckpoint(world)
        && XgbaE6SnapshotWorld(world))
        gSpecialVar_Result = 1;
}

// Native saves made inside cloned Hoenn should also refresh the E6 bank.
// No write occurs from Test Town, and older E5 ROMs never activate E6.
void XgbaE6CheckpointOnSave(void)
{
    u8 world = XgbaE6CurrentWorld();

    if (world < 2 || world > 20 || !XgbaE6Available())
        return;
    if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_XGBA_TEST_TOWN)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_XGBA_TEST_TOWN))
        return;

    if (XgbaE6BoxesCheckpoint(world))
        XgbaE6SnapshotWorld(world);
}

u8 XgbaE6GetSelectedWorld(void)
{
    return XgbaE6CurrentWorld();
}

s32 XgbaE6AuditWorld(u8 world)
{
    u8 slot;
    u32 sequence;
    u32 length;
    s32 status;

    if (world < 1 || world > 20 || !XgbaE6Available())
        return -1;

    status = XgbaE6SelectWorld(world, &slot, &sequence, &length);
    if (status == 1 && length != XgbaE6SnapshotSize())
        return -1;
    return status;
}

static u8 XgbaE6CurrentWorld(void)
{
    u16 world = VarGet(VAR_XGBA_WORLD_ID);

    if (world < 2 || world > 20)
        return 1;
    return world;
}

void XgbaE6SpecialSnapshot(void)
{
    gSpecialVar_Result = 0;
    if (!XgbaE6Available())
        return;

    if (XgbaE6SnapshotWorld(XgbaE6CurrentWorld()))
        gSpecialVar_Result = 1;
    else
        gSpecialVar_Result = 3;
}

void XgbaE6SpecialAudit(void)
{
    s32 result = XgbaE6AuditWorld(XgbaE6CurrentWorld());

    if (result == 1)
        gSpecialVar_Result = 1;
    else if (result == 0)
        gSpecialVar_Result = 2;
    else
        gSpecialVar_Result = 4;
}
