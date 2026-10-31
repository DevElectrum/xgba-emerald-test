#ifndef GUARD_XGBA_E6_H
#define GUARD_XGBA_E6_H

bool8 XgbaE6Available(void);
bool8 XgbaE6SnapshotWorld(u8 world);
bool8 XgbaE6RestoreWorld(u8 world);
s32 XgbaE6AuditWorld(u8 world);
void XgbaE6SpecialSnapshot(void);
void XgbaE6SpecialAudit(void);
void XgbaE6SpecialEnterWorld(void);
void XgbaE6SpecialLeaveWorld(void);
void XgbaE6CheckpointOnSave(void);

#endif
