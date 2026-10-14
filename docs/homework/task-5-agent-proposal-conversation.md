# Task 5: the agent's feature proposal

The agent's answer to the Director's prompt *"I want you to propose to me the most suitable feature to develop now."* The Scope Guardian read the GDD and the existing work, asked the Architect for advice, and returned this ranked proposal. The Q&A at the end discusses whether this was a goal-oriented agent at work.

---

The Scope Guardian recommends **A1, "Lives and falls"**, as the next feature. It consulted the Architect in Advice mode. It did not check Linear (the call was rejected), so I can't say whether the board and the files agree.

**What A1 is**
- The player gets 3 lives.
- A fall costs one life.
- After a fall the ship blinks and is invulnerable for 30 ticks.
- Lives show on the HUD.

**Why now**
- The ship can fall and respawn, but nothing costs a life, so the run can't be lost.
- The GDD's lose condition is "all lives lost", and week 1 of the schedule ends on "can die".
- It replaces the stand-in in DRA-6 that respawns with no life lost. DRA-6 is frozen, so A1 needs its own id, linked to DRA-6 as related.
- The Architect says A1 can be built on today's code at medium size, touching 5 to 6 systems. It changes the frozen `ship` and `app` contracts.
- Fit: it fits Pillar 1, Master the drift (no stun) and locked decisions 2, 4 and 5. It touches no other pillar, and nothing in the out-of-scope list.

**Runner-ups**
1. **A2, game over and retry.** The Architect recommends splitting A into A1 and A2. A2 needs your answers on the retry key and delay (FL-02), the game-over screen content (UI-04), and what "win" shows without saves (FL-03).
2. **C, control card (locked decision 8).** It is small and independent. It needs the start key (FL-01) and the card text and look (UI-03). The Architect suggests doing it after A, so it can reuse the same game-state shape.
3. **Not yet: B, the meteorite and Wave 0.** It is large and blocked. The meteorite size, hitbox, speed and telegraph (OBJ-01), Wave 0 (WV-05), the entry warning (OB-01) and despawn (OB-03) are all missing, and no collision or wave code exists. A hit means nothing without lives.

**GDD values A1 needs that are missing** (the guardian will not fill them in)
- LD-04: blink speed.
- LD-05: can a fall cost a life while the ship is invulnerable?
- UI-02 and UI-01: lives as icons or a number, and the top-right position, font and margins.
- LD-08: the screen flash, the breaking HUD life, and the ship burst and rebuild.
- LD-09: does the last life play the feedback before the stop?

These are already in the GDD: `lives_start` 3, `invuln_ticks` 30 and `fall_respawn` (320, 240).

**Questions for you**
1. Is A1 the feature to scope?
2. Should the full life-lost feedback (flash, breaking life, burst) be in A1 or out? The guardian suggests A1 ships with only the blink, and the full feedback becomes its own feature.
3. Should it check Linear for open issues and mismatches?

If you pick A1, the guardian creates the Linear issue and the scope report. I can continue it with your answers.

---

> Is this what just happened a goal oriented agent acting?

**Was that a goal-oriented agent acting? Partly.**

The goal-oriented part:
- It was given one goal: propose the best next feature.
- It chose its own steps. It read the GDD, past scope reports and contracts, and compared them.
- It spawned the Architect for technical advice.
- When the Linear call was rejected, it carried on and said so, instead of guessing.
- It stopped at a point where the Director has to decide.

The limits:
- Its procedure is mostly fixed by [scope-guardian.md](.claude/agents/scope-guardian.md). That file says what to read, when to consult the Architect, and what the report looks like.
- My prompt narrowed it further. I told it not to create a Linear issue or write a report.
- It can't ship anything without your approval. The rules make you the final call.

So it's a goal-directed agent working inside tight rules, more than a free-roaming one. It chose the steps within each stage, but the stages and the approval gates came from its definition.
