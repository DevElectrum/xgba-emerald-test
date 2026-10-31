#include "global.h"
#include "pokemon_storage_system.h"
#include "xgba_e6.h"

// Eight independent 0x8400-byte page records per world, with two A/B copies.
// World stride 0x88000 retains the original E6 eight-page bank allocation.
// Header and payloads are accessed via volatile bytes: XGBA's 0x0F mapping is
// byte-access only. The normal Emerald 14-box PC remains the only RAM copy.
#define XGBA_BOX_BASE ((volatile u8 *)0x0F360000)
#define XGBA_BOX_WORLD_STRIDE 0x88000
#define XGBA_BOX_RECORD_STRIDE 0x8400
#define XGBA_BOX_HEADER_SIZE 32
#define XGBA_BOX_META_OFFSET 0x84000
#define XGBA_BOX_META_STRIDE 0x40
#define XGBA_BOX_PAGES 8
#define XGBA_BOX_FORMAT_VERSION 2

typedef char XgbaBoxPayloadFits[
    sizeof(struct PokemonStorage) + XGBA_BOX_HEADER_SIZE <= XGBA_BOX_RECORD_STRIDE ? 1 : -1];
typedef char XgbaBoxLayoutFits[
    XGBA_BOX_PAGES * 2 * XGBA_BOX_RECORD_STRIDE + 2 * XGBA_BOX_META_STRIDE
        <= XGBA_BOX_WORLD_STRIDE ? 1 : -1];

static const u8 sPageMagic[8] = {'X', 'G', 'B', 'A', 'E', '6', 'P', 0};
static const u8 sMetaMagic[8] = {'X', 'G', 'B', 'A', 'E', '6', 'M', 0};
static const u8 sLegacyMagic[8] = {'X', 'G', 'B', 'A', 'E', '6', 'B', 0};

// In ROM, not EWRAM. Avoid eight bit-by-bit CRC rounds per stored byte.
static const u32 sCrcTable[256] =
{
    0x00000000U, 0x77073096U, 0xEE0E612CU, 0x990951BAU, 0x076DC419U, 0x706AF48FU, 0xE963A535U, 0x9E6495A3U,
    0x0EDB8832U, 0x79DCB8A4U, 0xE0D5E91EU, 0x97D2D988U, 0x09B64C2BU, 0x7EB17CBDU, 0xE7B82D07U, 0x90BF1D91U,
    0x1DB71064U, 0x6AB020F2U, 0xF3B97148U, 0x84BE41DEU, 0x1ADAD47DU, 0x6DDDE4EBU, 0xF4D4B551U, 0x83D385C7U,
    0x136C9856U, 0x646BA8C0U, 0xFD62F97AU, 0x8A65C9ECU, 0x14015C4FU, 0x63066CD9U, 0xFA0F3D63U, 0x8D080DF5U,
    0x3B6E20C8U, 0x4C69105EU, 0xD56041E4U, 0xA2677172U, 0x3C03E4D1U, 0x4B04D447U, 0xD20D85FDU, 0xA50AB56BU,
    0x35B5A8FAU, 0x42B2986CU, 0xDBBBC9D6U, 0xACBCF940U, 0x32D86CE3U, 0x45DF5C75U, 0xDCD60DCFU, 0xABD13D59U,
    0x26D930ACU, 0x51DE003AU, 0xC8D75180U, 0xBFD06116U, 0x21B4F4B5U, 0x56B3C423U, 0xCFBA9599U, 0xB8BDA50FU,
    0x2802B89EU, 0x5F058808U, 0xC60CD9B2U, 0xB10BE924U, 0x2F6F7C87U, 0x58684C11U, 0xC1611DABU, 0xB6662D3DU,
    0x76DC4190U, 0x01DB7106U, 0x98D220BCU, 0xEFD5102AU, 0x71B18589U, 0x06B6B51FU, 0x9FBFE4A5U, 0xE8B8D433U,
    0x7807C9A2U, 0x0F00F934U, 0x9609A88EU, 0xE10E9818U, 0x7F6A0DBBU, 0x086D3D2DU, 0x91646C97U, 0xE6635C01U,
    0x6B6B51F4U, 0x1C6C6162U, 0x856530D8U, 0xF262004EU, 0x6C0695EDU, 0x1B01A57BU, 0x8208F4C1U, 0xF50FC457U,
    0x65B0D9C6U, 0x12B7E950U, 0x8BBEB8EAU, 0xFCB9887CU, 0x62DD1DDFU, 0x15DA2D49U, 0x8CD37CF3U, 0xFBD44C65U,
    0x4DB26158U, 0x3AB551CEU, 0xA3BC0074U, 0xD4BB30E2U, 0x4ADFA541U, 0x3DD895D7U, 0xA4D1C46DU, 0xD3D6F4FBU,
    0x4369E96AU, 0x346ED9FCU, 0xAD678846U, 0xDA60B8D0U, 0x44042D73U, 0x33031DE5U, 0xAA0A4C5FU, 0xDD0D7CC9U,
    0x5005713CU, 0x270241AAU, 0xBE0B1010U, 0xC90C2086U, 0x5768B525U, 0x206F85B3U, 0xB966D409U, 0xCE61E49FU,
    0x5EDEF90EU, 0x29D9C998U, 0xB0D09822U, 0xC7D7A8B4U, 0x59B33D17U, 0x2EB40D81U, 0xB7BD5C3BU, 0xC0BA6CADU,
    0xEDB88320U, 0x9ABFB3B6U, 0x03B6E20CU, 0x74B1D29AU, 0xEAD54739U, 0x9DD277AFU, 0x04DB2615U, 0x73DC1683U,
    0xE3630B12U, 0x94643B84U, 0x0D6D6A3EU, 0x7A6A5AA8U, 0xE40ECF0BU, 0x9309FF9DU, 0x0A00AE27U, 0x7D079EB1U,
    0xF00F9344U, 0x8708A3D2U, 0x1E01F268U, 0x6906C2FEU, 0xF762575DU, 0x806567CBU, 0x196C3671U, 0x6E6B06E7U,
    0xFED41B76U, 0x89D32BE0U, 0x10DA7A5AU, 0x67DD4ACCU, 0xF9B9DF6FU, 0x8EBEEFF9U, 0x17B7BE43U, 0x60B08ED5U,
    0xD6D6A3E8U, 0xA1D1937EU, 0x38D8C2C4U, 0x4FDFF252U, 0xD1BB67F1U, 0xA6BC5767U, 0x3FB506DDU, 0x48B2364BU,
    0xD80D2BDAU, 0xAF0A1B4CU, 0x36034AF6U, 0x41047A60U, 0xDF60EFC3U, 0xA867DF55U, 0x316E8EEFU, 0x4669BE79U,
    0xCB61B38CU, 0xBC66831AU, 0x256FD2A0U, 0x5268E236U, 0xCC0C7795U, 0xBB0B4703U, 0x220216B9U, 0x5505262FU,
    0xC5BA3BBEU, 0xB2BD0B28U, 0x2BB45A92U, 0x5CB36A04U, 0xC2D7FFA7U, 0xB5D0CF31U, 0x2CD99E8BU, 0x5BDEAE1DU,
    0x9B64C2B0U, 0xEC63F226U, 0x756AA39CU, 0x026D930AU, 0x9C0906A9U, 0xEB0E363FU, 0x72076785U, 0x05005713U,
    0x95BF4A82U, 0xE2B87A14U, 0x7BB12BAEU, 0x0CB61B38U, 0x92D28E9BU, 0xE5D5BE0DU, 0x7CDCEFB7U, 0x0BDBDF21U,
    0x86D3D2D4U, 0xF1D4E242U, 0x68DDB3F8U, 0x1FDA836EU, 0x81BE16CDU, 0xF6B9265BU, 0x6FB077E1U, 0x18B74777U,
    0x88085AE6U, 0xFF0F6A70U, 0x66063BCAU, 0x11010B5CU, 0x8F659EFFU, 0xF862AE69U, 0x616BFFD3U, 0x166CCF45U,
    0xA00AE278U, 0xD70DD2EEU, 0x4E048354U, 0x3903B3C2U, 0xA7672661U, 0xD06016F7U, 0x4969474DU, 0x3E6E77DBU,
    0xAED16A4AU, 0xD9D65ADCU, 0x40DF0B66U, 0x37D83BF0U, 0xA9BCAE53U, 0xDEBB9EC5U, 0x47B2CF7FU, 0x30B5FFE9U,
    0xBDBDF21CU, 0xCABAC28AU, 0x53B39330U, 0x24B4A3A6U, 0xBAD03605U, 0xCDD70693U, 0x54DE5729U, 0x23D967BFU,
    0xB3667A2EU, 0xC4614AB8U, 0x5D681B02U, 0x2A6F2B94U, 0xB40BBE37U, 0xC30C8EA1U, 0x5A05DF1BU, 0x2D02EF8DU,

};

static u8 sCurrentWorld;
static u8 sCurrentPage;
static bool8 sBoxReady;

static u16 Read16(const volatile u8 *p)
{
    return (u16)p[0] | ((u16)p[1] << 8);
}

static u32 Read32(const volatile u8 *p)
{
    return (u32)p[0] | ((u32)p[1] << 8)
        | ((u32)p[2] << 16) | ((u32)p[3] << 24);
}

static void Write16(volatile u8 *p, u16 value)
{
    p[0] = value;
    p[1] = value >> 8;
}

static void Write32(volatile u8 *p, u32 value)
{
    p[0] = value;
    p[1] = value >> 8;
    p[2] = value >> 16;
    p[3] = value >> 24;
}

static u32 UpdateCrc(u32 crc, u8 byte)
{
    return sCrcTable[(crc ^ byte) & 0xFF] ^ (crc >> 8);
}

static u32 CrcVolatile(const volatile u8 *p, u32 length)
{
    u32 crc = 0xFFFFFFFF;
    u32 i;
    for (i = 0; i < length; i++)
        crc = UpdateCrc(crc, p[i]);
    return crc ^ 0xFFFFFFFF;
}

static u32 CrcRam(const u8 *p, u32 length)
{
    u32 crc = 0xFFFFFFFF;
    u32 i;
    for (i = 0; i < length; i++)
        crc = UpdateCrc(crc, p[i]);
    return crc ^ 0xFFFFFFFF;
}

static bool8 IsMagic(const volatile u8 *p, const u8 *magic)
{
    u32 i;
    for (i = 0; i < 8; i++)
    {
        if (p[i] != magic[i])
            return FALSE;
    }
    return TRUE;
}

static bool8 IsUnused(const volatile u8 *p)
{
    u32 i;
    for (i = 0; i < 8; i++)
    {
        if (p[i] != 0xFF)
            return FALSE;
    }
    return TRUE;
}

static volatile u8 *WorldBase(u8 world)
{
    return XGBA_BOX_BASE + (world - 1) * XGBA_BOX_WORLD_STRIDE;
}

static volatile u8 *PageRecord(u8 world, u8 page, u8 slot)
{
    return WorldBase(world) + (page * 2 + slot) * XGBA_BOX_RECORD_STRIDE;
}

static volatile u8 *MetaRecord(u8 world, u8 slot)
{
    return WorldBase(world) + XGBA_BOX_META_OFFSET + slot * XGBA_BOX_META_STRIDE;
}

// Read headers without hashing both full page payloads. Only the newest
// candidate needs a payload CRC; the other copy is fallback on corruption.
// Return 1 valid, 0 never initialized, -1 damaged.
static s8 PageHeader(u8 world, u8 page, u8 slot, u32 *seq, u32 *crc)
{
    const volatile u8 *p = PageRecord(world, page, slot);
    if (IsUnused(p))
        return 0;
    if (!IsMagic(p, sPageMagic)
        || Read16(p + 8) != XGBA_BOX_FORMAT_VERSION
        || Read16(p + 10) != world
        || p[12] != page || p[13] != 0 || Read16(p + 14) != 0
        || Read32(p + 20) != sizeof(struct PokemonStorage)
        || Read32(p + 28) != CrcVolatile(p, 28))
        return -1;

    *seq = Read32(p + 16);
    *crc = Read32(p + 24);
    return *seq != 0 ? 1 : -1;
}

static bool8 PagePayloadValid(u8 world, u8 page, u8 slot, u32 crc)
{
    return CrcVolatile(PageRecord(world, page, slot) + XGBA_BOX_HEADER_SIZE,
        sizeof(struct PokemonStorage)) == crc;
}

static s8 FindPage(u8 world, u8 page, u8 *slot, u32 *seq, u32 *crc)
{
    u32 seq0 = 0, seq1 = 0, crc0 = 0, crc1 = 0;
    s8 a = PageHeader(world, page, 0, &seq0, &crc0);
    s8 b = PageHeader(world, page, 1, &seq1, &crc1);
    u8 first = (b == 1 && (a != 1 || seq1 > seq0)) ? 1 : 0;

    if (first == 0 && a == 1 && PagePayloadValid(world, page, 0, crc0))
    {
        *slot = 0;
        *seq = seq0;
        *crc = crc0;
        return 1;
    }
    if (first == 1 && b == 1 && PagePayloadValid(world, page, 1, crc1))
    {
        *slot = 1;
        *seq = seq1;
        *crc = crc1;
        return 1;
    }
    if (first == 0 && b == 1 && PagePayloadValid(world, page, 1, crc1))
    {
        *slot = 1;
        *seq = seq1;
        *crc = crc1;
        return 1;
    }
    if (first == 1 && a == 1 && PagePayloadValid(world, page, 0, crc0))
    {
        *slot = 0;
        *seq = seq0;
        *crc = crc0;
        return 1;
    }
    if (a == 0 && b == 0)
        return 0;
    return -1;
}

static s8 MetaHeader(u8 world, u8 slot, u8 *page, u32 *seq)
{
    const volatile u8 *p = MetaRecord(world, slot);
    if (IsUnused(p))
        return 0;
    if (!IsMagic(p, sMetaMagic)
        || Read16(p + 8) != XGBA_BOX_FORMAT_VERSION
        || Read16(p + 10) != world
        || p[12] >= XGBA_BOX_PAGES
        || p[13] != 0 || Read16(p + 14) != 0
        || Read32(p + 20) != 0 || Read32(p + 24) != 0
        || Read32(p + 28) != CrcVolatile(p, 28))
        return -1;
    *page = p[12];
    *seq = Read32(p + 16);
    return *seq != 0 ? 1 : -1;
}

static s8 FindMeta(u8 world, u8 *slot, u8 *page, u32 *seq)
{
    u8 page0 = 0, page1 = 0;
    u32 seq0 = 0, seq1 = 0;
    s8 a = MetaHeader(world, 0, &page0, &seq0);
    s8 b = MetaHeader(world, 1, &page1, &seq1);

    if (a == 1 && (b != 1 || seq0 >= seq1))
    {
        *slot = 0;
        *page = page0;
        *seq = seq0;
        return 1;
    }
    if (b == 1)
    {
        *slot = 1;
        *page = page1;
        *seq = seq1;
        return 1;
    }
    return a == 0 && b == 0 ? 0 : -1;
}

static void WriteHeader(volatile u8 *p, const u8 *magic, u8 world,
    u8 page, u32 seq, u32 length, u32 crc)
{
    u32 i;
    Write16(p + 8, XGBA_BOX_FORMAT_VERSION);
    Write16(p + 10, world);
    p[12] = page;
    p[13] = 0;
    Write16(p + 14, 0);
    Write32(p + 16, seq);
    Write32(p + 20, length);
    Write32(p + 24, crc);
    for (i = 0; i < 8; i++)
        p[i] = magic[i];
    // This is the last write to make incomplete headers fail closed.
    Write32(p + 28, CrcVolatile(p, 28));
}

static bool8 WritePage(u8 world, u8 page)
{
    u8 oldSlot = 0;
    u32 seq = 0, oldCrc = 0, crc;
    u32 i;
    s8 status;
    volatile u8 *target;
    const u8 *live = (const u8 *)gPokemonStoragePtr;

    status = FindPage(world, page, &oldSlot, &seq, &oldCrc);
    if (status < 0 || seq == 0xFFFFFFFF)
        return FALSE;
    crc = CrcRam(live, sizeof(struct PokemonStorage));
    if (status == 1 && crc == oldCrc)
        return TRUE;

    target = PageRecord(world, page, status == 1 ? 1 - oldSlot : 0);
    for (i = 0; i < 8; i++)
        target[i] = 0xFF;
    // Invalidate header CRC before writing any payload. A/B protects old slot.
    Write32(target + 28, 0);
    for (i = 0; i < sizeof(struct PokemonStorage); i++)
        target[XGBA_BOX_HEADER_SIZE + i] = live[i];
    WriteHeader(target, sPageMagic, world, page, seq + 1,
        sizeof(struct PokemonStorage), crc);
    return TRUE;
}

static bool8 WriteMeta(u8 world, u8 page)
{
    u8 slot = 0, oldPage = 0;
    u32 seq = 0, i;
    s8 status = FindMeta(world, &slot, &oldPage, &seq);
    volatile u8 *p;

    if (status < 0 || seq == 0xFFFFFFFF)
        return FALSE;
    if (status == 1 && oldPage == page)
        return TRUE;
    p = MetaRecord(world, status == 1 ? 1 - slot : 0);
    for (i = 0; i < 8; i++)
        p[i] = 0xFF;
    Write32(p + 28, 0);
    WriteHeader(p, sMetaMagic, world, page, seq + 1, 0, 0);
    return TRUE;
}

// Old bank-format saves must be converted offline. Never reinitialize over
// unknown data or a damaged v2 page, even when the other world is usable.
bool8 XgbaE6BoxesCanEnterWorld(u8 world)
{
    u8 metaSlot = 0, page = 0, pageSlot = 0;
    u32 metaSeq = 0, pageSeq = 0, crc = 0;
    s8 meta, record;
    const volatile u8 *base;

    if (!XgbaE6Available() || world < 1 || world > 20)
        return FALSE;
    base = WorldBase(world);
    if (IsMagic(base, sLegacyMagic)
        || IsMagic(base + 0x44000, sLegacyMagic))
        return FALSE;
    meta = FindMeta(world, &metaSlot, &page, &metaSeq);
    if (meta < 0)
        return FALSE;
    if (meta == 0)
    {
        // New/unvisited world is genuinely blank only when both of the old
        // bank starts, the first v2 page, and the metadata are all erased.
        return IsUnused(base) && IsUnused(base + 0x44000)
            && IsUnused(PageRecord(world, 0, 1))
            && IsUnused(MetaRecord(world, 0))
            && IsUnused(MetaRecord(world, 1));
    }
    record = FindPage(world, page, &pageSlot, &pageSeq, &crc);
    return record == 1;
}

bool8 XgbaE6BoxesEnterWorld(u8 world)
{
    u8 metaSlot = 0, page = 0, slot = 0;
    u32 metaSeq = 0, pageSeq = 0, crc = 0, i;
    s8 meta;
    const volatile u8 *src;
    u8 *live = (u8 *)gPokemonStoragePtr;

    if (!XgbaE6BoxesCanEnterWorld(world))
        return FALSE;
    meta = FindMeta(world, &metaSlot, &page, &metaSeq);
    if (meta == 0)
    {
        // The caller has just restored this world's native page 1 from its
        // world snapshot. New pages are not silently imported from elsewhere.
        sCurrentWorld = world;
        sCurrentPage = 0;
        sBoxReady = TRUE;
        if (!WritePage(world, 0) || !WriteMeta(world, 0))
        {
            sBoxReady = FALSE;
            return FALSE;
        }
        return TRUE;
    }
    if (FindPage(world, page, &slot, &pageSeq, &crc) != 1)
        return FALSE;
    src = PageRecord(world, page, slot) + XGBA_BOX_HEADER_SIZE;
    for (i = 0; i < sizeof(struct PokemonStorage); i++)
        live[i] = src[i];
    sCurrentWorld = world;
    sCurrentPage = page;
    sBoxReady = TRUE;
    return TRUE;
}

static bool8 EnsureWorld(u8 world)
{
    if (sBoxReady && world == sCurrentWorld)
        return TRUE;
    return XgbaE6BoxesEnterWorld(world);
}

bool8 XgbaE6BoxesCheckpoint(u8 world)
{
    if (!EnsureWorld(world))
        return FALSE;
    return WritePage(world, sCurrentPage);
}

u8 XgbaE6BoxesGetPage(u8 world)
{
    if (!EnsureWorld(world))
        return 0;
    return sCurrentPage;
}

bool8 XgbaE6BoxesSwitchPage(u8 world, u8 nextPage)
{
    u8 slot = 0, oldPage;
    u32 seq = 0, crc = 0, i;
    s8 targetStatus;
    const volatile u8 *src;
    u8 *live = (u8 *)gPokemonStoragePtr;

    if (nextPage >= XGBA_BOX_PAGES || !EnsureWorld(world))
        return FALSE;
    if (nextPage == sCurrentPage)
        return TRUE;

    // Check target before modifying the current live page.
    targetStatus = FindPage(world, nextPage, &slot, &seq, &crc);
    if (targetStatus < 0)
        return FALSE;
    if (!WritePage(world, sCurrentPage))
        return FALSE;

    oldPage = sCurrentPage;
    if (targetStatus == 1)
    {
        src = PageRecord(world, nextPage, slot) + XGBA_BOX_HEADER_SIZE;
        for (i = 0; i < sizeof(struct PokemonStorage); i++)
            live[i] = src[i];
    }
    else
    {
        ResetPokemonStorageSystem();
    }

    sCurrentPage = nextPage;
    if (targetStatus == 0 && !WritePage(world, nextPage))
    {
        sCurrentPage = oldPage;
        XgbaE6BoxesEnterWorld(world);
        return FALSE;
    }
    if (!WriteMeta(world, nextPage))
    {
        sCurrentPage = oldPage;
        XgbaE6BoxesEnterWorld(world);
        return FALSE;
    }
    return TRUE;
}
