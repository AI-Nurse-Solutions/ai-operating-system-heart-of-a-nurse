# Setup cheatsheet — Hermes for nurse managers and entrepreneurs

Begin gently. One useful draft in your first week is enough.

## Before you start

- [ ] Took the SOUL quiz at https://nurse-ai-os.org/managers-entrepreneurs/
- [ ] Downloaded `SOUL.md` (and optionally `naio-soul.json`)
- [ ] Downloaded and unzipped this package
- [ ] Read `README.md` and `mission-control-packet/leader/DATA-BOUNDARY.md`

## 1 · Prepare a clean place to work

Use a dedicated computer if you can. If not, create a separate user account and one project folder. This keeps personal photos, finances, family messages, and saved logins out of reach. It reduces exposure; it is not a security sandbox.

Do not use a work computer without your employer's permission.

## 2 · Install Hermes Agent

Follow the current instructions for your operating system:

- https://hermes-agent.nousresearch.com/docs/getting-started/platform-support
- https://hermes-agent.nousresearch.com/desktop

Running Hermes on your computer does not make your data local. If you choose a cloud model, your prompts go to that provider. Choose deliberately.

## 3 · Put the files together

```bash
mkdir -p ~/Nurse-AI-OS/manager-entrepreneur
# unzip the package here, then move your SOUL files in:
mv ~/Downloads/SOUL.md ~/Downloads/naio-soul.json ~/Nurse-AI-OS/manager-entrepreneur/
```

## 4 · Place your SOUL (back up first)

Hermes reads its personality from `~/.hermes/SOUL.md`.

```bash
# back up any existing SOUL first
[ -f ~/.hermes/SOUL.md ] && cp ~/.hermes/SOUL.md ~/.hermes/SOUL.backup-$(date +%Y%m%d).md
cp ~/Nurse-AI-OS/manager-entrepreneur/SOUL.md ~/.hermes/SOUL.md
```

Or skip this step and let Hermes propose it in step 5. To undo, copy the backup back.

## 5 · First run

Open Hermes in the project folder and paste `HANDOFF-PROMPT.txt`. Hermes will summarize your SOUL, inventory the package, and propose one small task. Approve only what you understand.

## 6 · Your first week

| Day | Do this |
|---|---|
| Monday | Open `mission-control.html`. Set three priorities per lane. Export. |
| Monday | Ask Hermes: "Draft my weekly brief from this export. Keep it to one page." |
| Midweek | Pick one meeting. Ask for a draft from `templates/meeting-pack.md`. |
| Midweek (Build) | Ask for one validation step from `venture/30-Day-Validation-Sprint.md`. |
| Friday | Fill in the Friday review. Export. Ask Hermes what to carry forward. |

## Prompts that work

- "Using my SOUL, draft a one-page weekly brief from `mission-control-week.md`. Bottom line first."
- "Prepare a meeting pack for a staff huddle on [topic]. Use `templates/meeting-pack.md`. No names."
- "Turn my offer canvas into three customer interview questions. Do not write sales copy yet."
- "What in my week conflicts with protecting rest? Suggest one thing to drop."

## Stop and ask a human if

- a draft would include a patient, colleague, or client detail
- something would be sent, posted, scheduled, or paid for
- you are not sure you have the authority to decide it

Agents propose. Humans judge. Nurses steward.
