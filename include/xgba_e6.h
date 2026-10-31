#ifndef GUARD_XGBA_E6_H
#define GUARD_XGBA_E6_H

bool8 XgbaE6Available(void);
bool8 XgbaE6SnapshotWorld(u8 world);
s32 XgbaE6AuditWorld(u8 world);
void XgbaE6SpecialSnapshot(void);
void XgbaE6SpecialAudit(void);

#endif
