# Uninstall and Local Data Removal

These steps remove Nurse AI OS Mission Control 2.0.0 without removing the broader Nurse AI OS, unrelated role dashboards, or the optional legacy research specialization.

## Before removal

1. Decide whether any non-sensitive roles, missions, Soul Profile data, or capability evidence should be retained.
2. If needed, export the dashboard profile.
3. Open the JSON and remove or re-export anything prohibited or unnecessary.
4. Store the reviewed backup in an appropriate location.

The export is readable and unencrypted.

## Remove browser-local data

1. Open the exact Mission Control 2.0.0 origin you used.
2. Go to **My Role Dashboards**.
3. Choose **Reset all local personalization**.
4. Confirm the reset.
5. Close the page.

The application uses the storage key `discover.nurse-ai-os.mission-control.v2`. Storage is origin-specific, so portable `file://` mode and `http://127.0.0.1:43127` may have separate records. If you used both modes, open and reset each one.

If the dashboard no longer opens, use the browser's site-data controls to remove data for the exact local-file or `127.0.0.1:43127` origin. Review the browser's warning carefully; removing all site data can affect unrelated local applications on the same origin.

Downloaded backups, Soul templates, Markdown handoffs, screenshots, synced copies, browser backups, and device backups are separate files. Delete them intentionally where appropriate.

## Remove Hermes references

1. Give Hermes the scoped-removal section of `hermes/DISCOVER-Dashboard-Hermes-Integration-Installer.md`.
2. Ask Hermes to list every object it proposes to remove.
3. Confirm the objects belong only to `NAIOS-MISSION-CONTROL-LOCAL-2.0.0` under `nurse_ai_os.mission_control.*`.
4. Approve removal of only the local dashboard link, Guide reference, capability-state reference, and user-selected role child references.
5. Require a final residual inventory.

Do not remove the broader Nurse AI OS, permissions, agents, records, other role dashboards, or the `base-pack/` research specialization unless each is a separate explicit decision.

## Stop and delete the local package

1. If the local launcher is running, press `Control+C` in its terminal or command window.
2. Confirm the browser page no longer loads from `127.0.0.1:43127`.
3. Delete the `DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0` folder.
4. Empty Trash or Recycle Bin only when ready.
5. Delete obsolete ZIP files and backups where appropriate.

No uninstall program runs in the background. Removing a Hermes link does not delete local files or browser data; deleting the folder does not remove browser data or Hermes references.

## Verification

Uninstall is complete when:

- the local package folder is gone;
- the local launcher is stopped;
- the exact browser-local stores used by this release are cleared if requested;
- Mission Control 2.0.0 Hermes references are removed; and
- unrelated Nurse AI OS components remain unchanged.
