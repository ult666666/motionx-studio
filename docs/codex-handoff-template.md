# Codex Handoff Template

## Website Polish Pass

```text
Use the MOTIONX website-upgrade workflow. Read AGENTS.md, CLAUDE.md, and .agents/skills/motionx-website-upgrade/SKILL.md first. Improve only focused, high-confidence website copy/UI issues. Preserve section order, centralized content, concept labels, public hello@ contact, hero video preload="none", reduced-motion/data-saver poster behavior, and no fake proof. Do not push or deploy. Run npm run gate and npm run browser:verify, inspect screenshots, then commit locally if validated.
```

## Production Verification Pass

```text
Verify production read-only at https://madebymotionx.com. Do not push, deploy, or change Vercel/DNS/secrets/Gmail/CRM. Run PLAYWRIGHT_BASE_URL=https://madebymotionx.com npm run test:e2e and PLAYWRIGHT_BASE_URL=https://madebymotionx.com npm run browser:verify if network/browser approval is available. Curl /, /pilot, /system-study, /work/renewal, /work/liquid-signal, /work/furia, and /work/agentic-trading. Report pass/fail, screenshot observations, console errors, overflow, reduced motion, contact behavior, and concept label/disclosure visibility.
```

## Content-Integrity Update

```text
Update scripts/content-integrity.mjs for a specific new public content surface. Keep checks deterministic and avoid broad regex false positives. Preserve hello@ public contact, no founder/private email exposure, empty social links unless real, concept:true projects, visible Concept Project labels, concept disclosures, no fake proof, and no unsupported medical/health/product-efficacy claims. Run npm run content:check and npm run gate.
```

## Asset-Integrity Update

```text
Update docs/asset-integrity.md and scripts/asset-integrity.mjs for a specific intentional asset change. Never delete, rename, move, overwrite, or recompress root hf_2026*.mp4 masters. Public UI must reference public/videos derivatives and public/posters posters. If a size threshold changes, document the rationale. Run npm run assets:check and npm run gate.
```
