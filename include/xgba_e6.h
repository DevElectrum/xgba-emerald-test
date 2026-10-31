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
void XgbaE6SpecialLeaveWorldOne(void);
void XgbaE6SpecialReturnToWorldOne(void);
void XgbaE6CheckpointOnSave(void);
extern const u32 gXgbaE6CrcTable[256];
bool8 XgbaE6BoxesCanEnterWorld(u8 world);
bool8 XgbaE6BoxesEnterWorld(u8 world);
bool8 XgbaE6BoxesCheckpoint(u8 world);
bool8 XgbaE6BoxesCheckpointNativeWorldOne(void);
bool8 XgbaE6BoxesSwitchPage(u8 world, u8 page);
u8 XgbaE6BoxesGetPage(u8 world);
u8 XgbaE6GetSelectedWorld(void);

#endif
