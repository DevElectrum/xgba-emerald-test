#ifndef GUARD_XGBA_MAP_COMPAT_H
#define GUARD_XGBA_MAP_COMPAT_H

// Hoenn 2-20 reuse 34 cloned map groups (34..67) while keeping the
// original per-group map numbers. Use this only when matching original
// map tables or scripting special cases, NEVER when addressing live
// object events, changing active maps or writing save/warp identities.
static inline s16 XgbaCanonicalMapGroup(s16 group)
{
    if (group >= 34 && group < 68)
        return group - 34;
    return group;
}

#endif // GUARD_XGBA_MAP_COMPAT_H
