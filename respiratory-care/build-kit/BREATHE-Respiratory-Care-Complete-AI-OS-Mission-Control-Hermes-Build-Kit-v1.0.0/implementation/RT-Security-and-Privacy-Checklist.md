
# Security and Privacy Checklist

- [ ] Loopback-only binding and private authentication
- [ ] Server-owned sessions; secure cookies; rotation and timeout
- [ ] CSRF, Origin and Host validation
- [ ] Secrets server-side and excluded from logs/exports/backups
- [ ] Data admission before persistence and provider/agent calls
- [ ] Possible patient content rejected without echo or derived residue
- [ ] Live device, alarm, waveform, setting, serial-number, device-export and device-control content rejected before echo, persistence or provider/agent use
- [ ] No clinical, prescribing, ordering, coding, billing or claims executor
- [ ] Separate foundation/overlay namespaces and context isolation
- [ ] Encrypted transport to any approved local/remote provider
- [ ] File type, size, malware, rights and content admission controls
- [ ] Prompt injection cannot change policy, tools or permissions
- [ ] PERM-P0 default; exact ORBIT controls for P1–P4; personal P4 unavailable; P5 prohibited
- [ ] Visible Stop, Kill, Pause All and Safe Reset
- [ ] No hidden retry, recursion or background continuation
- [ ] Log minimization, rotation, inspection and deletion
- [ ] Backup/restore/update/rollback/uninstall tested
- [ ] Dependency lock, license inventory and SBOM
- [ ] Keyboard, screen reader, noncolor status, contrast, zoom/reflow, reduced motion and plain-language error tests
- [ ] Clean-machine tests for every claimed OS version
- [ ] Threat model and negative tests retained in final evidence
