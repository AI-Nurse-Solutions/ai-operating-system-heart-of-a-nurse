# The Pre-Procedure Checklist & Hermes Cheat Sheet

> You'd never start a procedure without the time-out: right patient, right site, right equipment. Give your AI setup the same respect. Keep this beside you for your first week. Menus move as Hermes updates — when something looks different, the official docs are the truth: https://hermes-agent.nousresearch.com/docs

## The one rule before anything
**No patient data. Ever.** No names, charts, screenshots, room numbers, or stories that could identify a patient. Hermes works on *your* life — learning, schedule, projects — never your patients.

## The time-out — verify before you begin
You check your equipment at the start of every shift. Same here — two minutes now saves an hour of frustration later.

**You need a desktop or laptop** — Mac or Windows. Not a phone, tablet, or Chromebook. Here's why it's worth it: on your own computer, your files and your AI's memory stay **local — on your machine, not in someone's cloud**. That's the whole point of owning your system.

**Rough guide:** a computer from the last ~5 years with at least 8 GB of memory and a few GB of free disk space usually does fine. The official Hermes site lists current requirements — check there before downloading.

**If Hermes won't install, it's your computer's specs — not you, and not a mistake you made.** A cloud option (we call it the VPS path) is coming so any device can run a full system. Until then, skip to "While you wait" at the bottom of this sheet — there's a whole on-ramp for you.

## 0.5 · Prep the field
Before any sterile procedure, you clear the field. Do the same for your AI:

- Create one dedicated home for this system (your `My-Nurse-AI-OS` folder — the Starter Kit builds it for you, and Documents is the perfect place for it).
- Make sure **nothing private lives inside that folder** — no tax documents, no family photos, no saved work files. The folder should contain only what you'd be comfortable letting an assistant read, because that's exactly what it is.
- If your computer is a family computer, consider a separate user account for your AI work — like having your own med cart instead of sharing one.

## 1 · Install
1. Go to the official Hermes site: https://hermes-agent.nousresearch.com/
2. Download Hermes for your computer (Mac or Windows) and follow their install steps.
3. Open it. When setup asks about an AI model/provider, read section 1.7 below first — there are free and low-cost routes.

## 1.5 · Permissions — give it a room, not the house
At some point Hermes will ask for permission to access files. This is the moment that matters most:

- **Grant access ONLY to your `My-Nurse-AI-OS` folder** — the one from the Starter Kit. Nothing else.
- Decline anything broader — full disk, Desktop, Downloads, Photos. If you accidentally grant more, you can remove it later in your computer's privacy settings.
- Think of it like a float nurse's badge: access to the assigned unit, not every floor of the hospital. Hermes does excellent work in its unit. It has no business wandering the building.

## 1.7 · Choose how your AI is powered — free and low-cost routes
**Hermes itself is free and open-source.** Any cost comes from the AI model that powers it — think of Hermes as the IV pump, free, and the model as what runs through it, metered by use. Two routes:

**Route A — the Nous subscription.** The simplest: one subscription, everything handled. Choose it during setup and skip the rest of this step.

**Route B — Bring Your Own Keys (most cost-effective — can be nearly free).** In Hermes setup, choose **Full Setup** (not the default subscription option), then **Bring Your Own Keys**. We recommend OpenRouter (https://openrouter.ai) — one free account, one API key, and a whole menu of models, including free and very low-cost ones. Then:

1. Create an account at openrouter.ai and generate an API key from your dashboard.
2. **Set a spending limit in OpenRouter first** — your safety rail against surprise bills. Start at a few dollars; you can always raise it.
3. In Hermes setup, choose OpenRouter as your provider and paste your key.
4. Pick a model — start with a free or low-cost one. Ask Hermes for something simple to confirm it works; if the answers feel weak, switch to a stronger model. Trying models costs nothing but the tokens you use.

**One caution:** a ChatGPT Plus or Grok subscription usually does *not* include API access — that's billed separately. The safest setup is a dedicated OpenRouter key with a spending limit you set yourself.

## 2 · Your first conversation
- Hermes works like a chat: type, press enter.
- Say hello and tell it who you are: *"I'm a nurse setting up my Nurse AI OS. I'll give you my SOUL file next — treat it as my standing instructions."*
- You cannot break anything by chatting.

## 3 · Give Hermes your SOUL file
Your SOUL file comes from the SOUL Quiz at nurse-ai-os.org (it downloads as `Core-SOUL.md`, or grab the whole bundle).
- Easiest way: attach or drag the file into the chat, or paste its contents.
- Then say: *"This is my SOUL file. Treat it as my standing instructions for how to support me. Confirm what you understood about my values and boundaries."*
- Read its summary back. Correct anything wrong — corrections stick.

## 4 · Give Hermes your Starter Kit
The Starter Kit (ZIP from nurse-ai-os.org) is the folder skeleton of your system.
- Unzip it somewhere you'll find again (Documents is perfect). The folder is `My-Nurse-AI-OS`.
- Tell Hermes: *"My Nurse AI OS folder is at [location]. This is where my files live: my SOUL file, my notes (03-Memory), my projects (04-Projects). Keep your work for me inside it."*

> **Why these two files matter more than everything else:** a powerful AI is like a powerful horse — magnificent, and dangerous without a harness. The Starter Kit and your SOUL file **are the harness.** The SOUL file gives the engine your values, your boundaries, the lines it may never cross. The Starter Kit gives it a home and a structure. Together they give the system **the heart of a nurse** — and keep the horse from running away with you. Skipping them doesn't make you faster; it makes you a passenger.

## 4.5 · Smart habit — a fresh Gmail for your AI life
Just like you don't do your personal banking from the unit's charting station, keep your AI life in its own lane:

- Create a free, separate Gmail account (something like `yourname.ai@gmail.com`) used only for your AI work, courses, and community.
- Your personal and family email stays private and separate — nothing crosses over.
- Bonus: that account comes with free Google Drive and Docs, which pair beautifully with your system later — a place for the drafts, plans, and projects your AI helps you build.

## 5 · Build your dashboard (one prompt)
Paste this:
> *"Using my SOUL file, personalize the Local HTML Life Dashboard in my starter kit (08-Integrations/Local-HTML-Life-Dashboard). Fill in my name, my top priorities in each sphere, and my first goals and habits from my quiz answers. Save it as My-Dashboard.html in my Nurse AI OS folder and tell me exactly where it is."*

Open the file it creates in your browser and **bookmark it**. That's your station board.

## Five phrases that do most of the work
| You say | Hermes does |
|---|---|
| "Run my morning huddle." | Asks your #1 priority, offers three ways to help |
| "Give me a Kardex entry for this session." | Writes a 5-line handoff note to save in 03-Memory |
| "Make that correction permanent." | Turns your feedback into a standing rule |
| "Before you start, interview me like an admission assessment." | Asks questions before big tasks instead of guessing |
| "Show me your plan before you do anything." | Keeps your hand on every decision |

## While you wait — no qualifying computer yet? You're still in.
If your current computer can't run Hermes, you've lost nothing but the installation step. Everything else is open to you today:

- **Take the free AI course** and browse the **55 free AI mentors** (CCRN and certification prep, leadership, career) — they run in any browser: nurse-ai-os.org/ai-mentors.html
- **Come to the monthly Lamp Huddle** and join the community list at nurse-ai-os.org
- **Take the SOUL Quiz now** — your SOUL file will be ready and waiting the day your system is

And hear this plainly: **your participation and your voice matter to us now — not after you buy hardware.** AI is coming to healthcare with or without nursing at the table. The nurses preparing today are the ones who will lead that change instead of being led by it. You are the future Florence Nightingales — the ones who will decide how care intelligence is born.

## If you feel lost
Normal. You only need the next step, never the whole map. Skip what confuses you, and bring questions to the monthly Lamp Huddle — every nurse there started exactly where you are.

*Agents propose. Humans judge. Nurses steward.* · © NAIO Institute · Not medical advice · No PHI
