
# Respiratory Care Professional BREATHE Agent Team and Routing

The canonical Respiratory Care Professional sources define systems and workflows, not autonomous agents. The ten-agent registry is an implementation-generated, restrictive routing aid. All agents install `PERM-P0 Disabled`.

## Routing rules

- Choose no agent when offline/local controls can complete the task.
- Select one primary agent from the user's requested outcome and active task hat/workspace/context.
- Show the routing reason and allow owner override or no-agent mode.
- A second agent may review only under a frozen charter; it receives no hidden context.
- The independent auditor uses a separate control path and cannot approve the work it generated.
- No recursive delegation, shared hidden memory, background continuation or self-expansion.

## One-run charter

Freeze purpose, owner, active task hat/workspace/context, admitted data, exact sources, tools, model, time/token/cost/retry limits, output type, EDENA state, prohibited actions, human gates, stop/kill/fallback, expiry and receipt. P1 reads admitted context and explains. P2 drafts or runs a fictional simulation. Both permit one invocation, zero hidden retries and automatic return to P0.

PERM-P3 is an exact institution-approved read or sandbox. PERM-P4 is unavailable personally and can only stage one exact nonclinical administrative, education or quality-project action in an approved institutional destination for named-human release. PERM-P5 and every clinical, EHR, order, event, message, paging or device destination are prohibited.

See `config/RT-Agent-Registry.v1.json` for the exact ten IDs and ceilings.
