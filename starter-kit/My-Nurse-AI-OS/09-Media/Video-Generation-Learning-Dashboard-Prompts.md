# Video Generation for Learning Dashboards

Video generation is optional and advanced. Use it mainly for short, low-distraction loops, not long clinical explainers.

## Setup concept

- Enable video tools through `hermes tools` when available.
- Use Nous Tool Gateway when supported or a direct provider key such as FAL for video models.
- Keep generated clips short and non-distracting.
- Treat costs as variable and check provider pricing before repeated generation.

## Best use cases

- 4–8 second ambient learning dashboard loops
- subtle knowledge graph motion
- study timer background
- daily review loop
- gentle image-to-video animation from an already approved still image

## Design rules

- Prefer slow drift, pulse, glow, or parallax.
- Avoid fast cuts or dramatic camera movement.
- Avoid text inside videos unless the model handles typography well.
- Do not use patient images, clinical screenshots, or PHI.
- Use human review before publishing.

## Starter prompts

```text
Create a 6-second seamless loop for a learning dashboard background: soft blue and slate abstract gradients, gentle particle drift, minimal motion, clean modern interface aesthetic, no text, 16:9.
```

```text
Generate a subtle animated concept visual for a note-taking dashboard: interconnected nodes and faint lines pulsing slowly like a knowledge graph, calm and readable, dark-mode friendly, seamless 8-second loop, no text.
```

```text
Animate this existing dashboard hero image into a 5-second loop with slow parallax, slight glow movement, and gentle depth. Preserve the original composition and keep motion subtle.
```
