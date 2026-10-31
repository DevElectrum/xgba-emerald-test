#ifndef GUARD_XGBA_E5_H
#define GUARD_XGBA_E5_H

bool8 XgbaE5Available(void);
s32 XgbaE5ReadWorld(u8 world, u8 *destination, u16 capacity, u16 *length);
bool8 XgbaE5WriteWorld(u8 world, const u8 *source, u16 length);
void XgbaE5SpecialSnapshot(void);
void XgbaE5SpecialAudit(void);

#endif
