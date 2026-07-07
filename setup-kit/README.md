# Nurse AI OS Setup Kit

Reusable operational assets for setting up an AI-assisted workstation (Cowork, Claude Code, or any Claude surface) the Nurse AI OS way. Models change; this kit is what you own.

## Contents

### Contents of this folder

**architect-mode.skill** — the flagship operating process. Wraps any complex or high-stakes task in five gates (Scope → Evidence → Attack → Verify → Report), separates orchestration from execution (expensive reasoning plans and verifies; cheaper models do the work), and captures winning processes as reusable assets. Fully generic — works for any team, not just Nurse AI OS.

To install: open the `.skill` file in a Claude chat (drag it in or use the file card) and click **Save skill**. It then triggers automatically on complex work, or invoke it directly with `/architect-mode`.

**source/** — editable source (SKILL.md + eval prompts) so the skill can be modified and re-packaged.

Tested 2026-07-07: with-skill runs passed 13/13 quality assertions vs 12/13 baseline; clearest gain was flagging assumptions and confidence levels instead of stating invented figures as fact. Overhead: roughly +28s and +5k tokens per task.
