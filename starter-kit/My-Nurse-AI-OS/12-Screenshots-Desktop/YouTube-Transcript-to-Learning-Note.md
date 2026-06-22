# YouTube Transcript to Learning Note

YouTube is a strong learning input for a personal AI OS. Hermes can convert lectures, tutorials, demos, and interviews into structured notes.

## Method choices

| Situation | Best method |
|---|---|
| Single video, quick summary | bundled YouTube content skill |
| Repeated video learning workflow | reusable YouTube-to-note skill |
| Many videos or automation | API-based transcript service only if needed |
| No setup | copy YouTube transcript manually and paste into Hermes |

## One-video prompt

```text
Use the YouTube content workflow for this video.
Fetch or process the transcript if available.
Create a structured learning note with:
1. title and source URL
2. timestamped chapter outline
3. 10-bullet summary
4. key concepts
5. practical applications for a personal AI OS
6. questions I should ask next
7. no-PHI / clinical safety considerations if healthcare is mentioned
```

## Obsidian-ready prompt

```text
Turn this YouTube lecture into an Obsidian-ready markdown note.
Include frontmatter, source URL, topic tags, timestamped chapters, key claims, what to verify, practical takeaways, and follow-up questions.
Keep claims grounded in the transcript. Do not invent citations.
```

## Healthcare video prompt

```text
Summarize this healthcare-related YouTube video as education only.
Separate claims, evidence, anecdotes, uncertainty, and practical implications.
Do not produce patient-specific medical advice.
Flag anything that would require checking guidelines, institutional policy, or licensed clinical judgment.
```

## Boundary

> YouTube transcripts are learning material, not clinical authority. Hermes can structure and question the content; humans verify and decide.
