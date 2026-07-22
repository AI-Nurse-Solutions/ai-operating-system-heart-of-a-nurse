# Read This First — Nurse AI OS Mission Control 2.0.0

This download is a real, local Mission Control dashboard for a Hermes-powered Nurse AI OS. It opens on your computer, keeps its code and assets in this folder, and prepares reviewable Markdown handoffs for Hermes. It is not a cloud service, clinical system, autonomous agent, or institutional enforcement platform.

## Allow enough time

The dashboard itself normally opens in seconds. First-run review, role setup, Discover Packet and Soul Profile personalization, backup review, and optional Hermes registration may take **several minutes**. Hermes integration may require **multiple visible, reviewed turns**. Keep the dashboard and Hermes windows open, read each proposed change, and wait for a final report.

Nothing in this package continues in the background. A session-only mission exists only in the open page and may disappear when that page reloads or closes.

## Install in this exact order

1. **Unzip the complete package.** Do not run it from inside the ZIP. Keep `index.html`, `assets/`, `guide/`, `hermes/`, and the launchers together.
2. **Choose a safe location.** Use a personal or organization-approved folder. Do not place the package in a shared, synced, or publicly indexed folder unless that location is approved for the information you intend to store.
3. **Review the safety boundary.** Do not enter protected health information (PHI), confidential institutional or research information, credentials, secrets, or sensitive personal data. Browser `localStorage` is unencrypted.
4. **Open Mission Control.** Use the launcher for your operating system, or open `index.html` directly:
   - macOS: `Start-DISCOVER.command`
   - Windows: `Start-DISCOVER.bat`
   - Linux: `./start-discover.sh`
5. **Complete the first-run walkthrough.** Acknowledge the local-storage boundary and read the human-approval rules.
6. **Create your Role Constellation.** Select one primary role and any supporting, emerging, or contextual roles. A role dashboard is a workspace view; it does not verify a credential or grant authority.
7. **Apply the Discover Packet only when ready.** Import a reviewed, derived `NAIO-DISCOVER-PACKET-ADAPTER-1` JSON—not raw interview notes. Preview its mission, goals, role priorities, workflow recommendations, AI boundaries and safe defaults before applying.
8. **Apply Soul personalization only when ready.** Import a reviewed, derived Soul Profile JSON through the versioned adapter. The quiz is being redesigned, so the included legacy demonstration is provisional. Raw quiz answers should not be imported.
9. **Start a non-sensitive mission.** Use Assess → Define/Diagnose → Plan → Implement → Evaluate. Begin with the synthetic sample if you want a safe walkthrough.
10. **Back up deliberately.** Export the dashboard profile and inspect the JSON. The export may include locally saved mission text and is not encrypted.
11. **Connect to Hermes only after local review.** Give Hermes `hermes/DISCOVER-Dashboard-Hermes-Integration-Installer.md`. Supply the exact local path when asked. Approve only changes Hermes shows you.
12. **Confirm the final integration state.** A valid result may be a local link, a Guide reference, or manual handoff only. A link is not proof of live synchronization or execution.

## Important distinctions

- **Personal Edition:** EDENA classifications are advisories and review gates. Red permits only deliberately acknowledged, sanitized sandbox exploration; it does not approve real-world use.
- **Institutional policy preview:** The dashboard demonstrates stricter stopping behavior, but a static local app is not tamper-resistant institutional enforcement. Real enforcement requires institution-controlled identity, policy, audit, approvals, and technical controls.
- **Capabilities and badges:** These are evidence-based development records. They are not licensure, certification, continuing-education credit, clinical competence verification, or permission to practice.
- **Hermes handoffs:** Copying or downloading a prompt does not send or execute it. The user pastes it into Hermes and reviews the response manually.

## Optional legacy research specialization

The `base-pack/` folder contains an earlier DISCOVER package for Healthcare Research & Innovation Leaders. It is an **optional role specialization**, not the universal Nurse AI OS core and not a prerequisite for this Mission Control. Install it only if that research/innovation lane fits your work and after reviewing its narrower rules.

Continue with `guide/DISCOVER-Mission-Control-Setup-Guide.md` for the full setup, backup, update, rollback, and troubleshooting instructions.
