#include "global.h"
#include "event_data.h"
#include "xgba_e5.h"

#define XGBA_E5_BASE ((volatile u8 *)0x0F000000)
#define XGBA_E5_SLOT_SIZE 0x5000
#define XGBA_E5_DATA_SIZE (XGBA_E5_SLOT_SIZE - 32)
#define XGBA_E5_FIRST_SLOT 0x1000
#define XGBA_E5_BACKUP_HEADER 0xDF000
#define XGBA_E4_SAVE_MAGIC 0x34454758

static const u8 sXgbaE5Header[24] = {
    'X', 'G', 'B', 'A', 'E', '5', 'S', 0,
    1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 16, 0,
    0xFE, 0xB1, 0x7D, 0x49
};

static const u8 sXgbaE5RecordMagic[8] = {
    'X', 'G', 'B', 'A', 'E', '5', 'W', 0
};

static u32 XgbaE5Read32(const volatile u8 *source)
{
    return (u32)source[0] | ((u32)source[1] << 8)
        | ((u32)source[2] << 16) | ((u32)source[3] << 24);
}

static u16 XgbaE5Read16(const volatile u8 *source)
{
    return (u16)source[0] | ((u16)source[1] << 8);
}

static void XgbaE5Write32(u8 *target, u32 value)
{
    target[0] = value;
    target[1] = value >> 8;
    target[2] = value >> 16;
    target[3] = value >> 24;
}

static void XgbaE5Write16(u8 *target, u16 value)
{
    target[0] = value;
    target[1] = value >> 8;
}

static u32 XgbaE5Crc32(const volatile u8 *source, u32 length)
{
    u32 crc = 0xFFFFFFFF;
    u32 i;
    u32 j;

    for (i = 0; i < length; i++)
    {
        crc ^= source[i];
        for (j = 0; j < 8; j++)
        {
            if (crc & 1)
                crc = (crc >> 1) ^ 0xEDB88320;
            else
                crc >>= 1;
        }
    }
    return crc ^ 0xFFFFFFFF;
}

static bool8 XgbaE5HeaderValid(u32 offset)
{
    u32 i;
    const volatile u8 *header = XGBA_E5_BASE + offset;

    for (i = 0; i < sizeof(sXgbaE5Header); i++)
    {
        if (header[i] != sXgbaE5Header[i])
            return FALSE;
    }
    return TRUE;
}

bool8 XgbaE5Available(void)
{
    const volatile u8 *rom = (const volatile u8 *)0x08000000;
    const u8 tag[7] = { 'X', 'G', 'B', 'A', '2', '5', '6' };
    u32 i;

    if (rom[0xBC] != 0xE5)
        return FALSE;
    for (i = 0; i < sizeof(tag); i++)
    {
        if (rom[0xB5 + i] != tag[i])
            return FALSE;
    }
    return XgbaE5HeaderValid(0) || XgbaE5HeaderValid(XGBA_E5_BACKUP_HEADER);
}

static volatile u8 *XgbaE5Slot(u8 world, u8 slot)
{
    u32 offset = XGBA_E5_FIRST_SLOT
        + ((world - 1) * 2 + slot) * XGBA_E5_SLOT_SIZE;
    return XGBA_E5_BASE + offset;
}

// Return -1 for corruption, 0 for an unused slot, 1 for a valid record.
static s32 XgbaE5InspectSlot(u8 world, u8 slot, u32 *sequence, u32 *length)
{
    const volatile u8 *record = XgbaE5Slot(world, slot);
    u32 i;
    bool8 empty = TRUE;

    for (i = 0; i < XGBA_E5_SLOT_SIZE; i++)
    {
        if (record[i] != 0xFF)
        {
            empty = FALSE;
            break;
        }
    }
    if (empty)
        return 0;
    for (i = 0; i < sizeof(sXgbaE5RecordMagic); i++)
    {
        if (record[i] != sXgbaE5RecordMagic[i])
            return -1;
    }
    if (XgbaE5Read16(record + 8) != 1 || XgbaE5Read16(record + 10) != world)
        return -1;
    *sequence = XgbaE5Read32(record + 12);
    *length = XgbaE5Read32(record + 16);
    if (*sequence == 0 || *length > XGBA_E5_DATA_SIZE
        || XgbaE5Read32(record + 28) != 0)
        return -1;
    if (XgbaE5Crc32(record, 24) != XgbaE5Read32(record + 24))
        return -1;
    if (XgbaE5Crc32(record + 32, *length) != XgbaE5Read32(record + 20))
        return -1;
    return 1;
}

static s32 XgbaE5SelectWorld(u8 world, u8 *slot, u32 *sequence, u32 *length)
{
    s32 first;
    s32 second;
    u32 firstSeq = 0;
    u32 secondSeq = 0;
    u32 firstLen = 0;
    u32 secondLen = 0;

    first = XgbaE5InspectSlot(world, 0, &firstSeq, &firstLen);
    second = XgbaE5InspectSlot(world, 1, &secondSeq, &secondLen);
    if (first == 1 && (second != 1 || firstSeq >= secondSeq))
    {
        *slot = 0;
        *sequence = firstSeq;
        *length = firstLen;
        return 1;
    }
    if (second == 1)
    {
        *slot = 1;
        *sequence = secondSeq;
        *length = secondLen;
        return 1;
    }
    if (first < 0 || second < 0)
        return -1;
    *slot = 1;
    *sequence = 0;
    *length = 0;
    return 0;
}

s32 XgbaE5ReadWorld(u8 world, u8 *destination, u16 capacity, u16 *length)
{
    u8 slot;
    u32 sequence;
    u32 size;
    u32 i;
    s32 status;
    const volatile u8 *source;

    if (world < 1 || world > 20 || !XgbaE5Available())
        return -1;
    status = XgbaE5SelectWorld(world, &slot, &sequence, &size);
    if (status != 1)
        return status;
    if (size > capacity || (size && destination == NULL))
        return -1;
    source = XgbaE5Slot(world, slot) + 32;
    for (i = 0; i < size; i++)
        destination[i] = source[i];
    if (length != NULL)
        *length = size;
    return 1;
}

bool8 XgbaE5WriteWorld(u8 world, const u8 *source, u16 length)
{
    u8 slot;
    u32 sequence;
    u32 previousLength;
    u32 i;
    u8 header[32];
    volatile u8 *target;
    s32 status;

    if (world < 1 || world > 20 || length > XGBA_E5_DATA_SIZE
        || (length && source == NULL) || !XgbaE5Available())
        return FALSE;
    status = XgbaE5SelectWorld(world, &slot, &sequence, &previousLength);
    if (status < 0 || sequence == 0xFFFFFFFF)
        return FALSE;

    target = XgbaE5Slot(world, status == 1 ? 1 - slot : 0);
    for (i = 0; i < 32; i++)
        target[i] = 0xFF;
    for (i = 0; i < length; i++)
        target[32 + i] = source[i];
    for (; i < XGBA_E5_DATA_SIZE; i++)
        target[32 + i] = 0xFF;

    memset(header, 0, sizeof(header));
    memcpy(header, sXgbaE5RecordMagic, sizeof(sXgbaE5RecordMagic));
    XgbaE5Write16(header + 8, 1);
    XgbaE5Write16(header + 10, world);
    XgbaE5Write32(header + 12, sequence + 1);
    XgbaE5Write32(header + 16, length);
    XgbaE5Write32(header + 20, XgbaE5Crc32(source, length));
    XgbaE5Write32(header + 24, XgbaE5Crc32(header, 24));
    for (i = 8; i < sizeof(header); i++)
        target[i] = header[i];
    for (i = 0; i < sizeof(sXgbaE5RecordMagic); i++)
        target[i] = header[i];
    return TRUE;
}

static u8 XgbaE5CurrentWorld(void)
{
    u16 world = VarGet(VAR_XGBA_WORLD_ID);

    if (world < 2 || world > 20)
        return 1;
    return world;
}

static const struct XgbaWorldEventState *XgbaE5CurrentE4State(void)
{
    u8 world = XgbaE5CurrentWorld();

    VarGet(VAR_XGBA_E4_PROGRESS);
    if (gSaveBlock1Ptr->xgbaWorldStateBank.magic != XGBA_E4_SAVE_MAGIC)
        return NULL;
    return &gSaveBlock1Ptr->xgbaWorldStateBank.worlds[world - 1];
}

void XgbaE5SpecialSnapshot(void)
{
    const struct XgbaWorldEventState *state;

    gSpecialVar_Result = 0;
    if (!XgbaE5Available())
        return;
    state = XgbaE5CurrentE4State();
    if (state == NULL)
    {
        gSpecialVar_Result = 3;
        return;
    }
    if (!XgbaE5WriteWorld(XgbaE5CurrentWorld(), (const u8 *)state, sizeof(*state)))
    {
        gSpecialVar_Result = 3;
        return;
    }
    gSpecialVar_Result = 1;
}

void XgbaE5SpecialAudit(void)
{
    const struct XgbaWorldEventState *state;
    struct XgbaWorldEventState saved;
    u16 length = 0;
    s32 status;

    gSpecialVar_Result = 0;
    if (!XgbaE5Available())
        return;
    state = XgbaE5CurrentE4State();
    if (state == NULL)
    {
        gSpecialVar_Result = 4;
        return;
    }
    status = XgbaE5ReadWorld(XgbaE5CurrentWorld(), (u8 *)&saved, sizeof(saved), &length);
    if (status == 0)
        gSpecialVar_Result = 2;
    else if (status < 0 || length != sizeof(saved))
        gSpecialVar_Result = 4;
    else if (memcmp(&saved, state, sizeof(saved)) != 0)
        gSpecialVar_Result = 3;
    else
        gSpecialVar_Result = 1;
}
