Verdict: ship
Created by: scope-guardian
Feature: DRA-23 Lives, falls, game over and retry
Parent: DRA-6

## Request
"I want you to propose to me the most suitable feature to develop now."

The Director then chose candidate A1, "Lives and falls", from the guardian's proposal. The main session relayed that choice. The Director then added the respawn wait, the Game Over box and the retry in direct messages (see Decision log).

## Feature
The ship has 3 lives, shown in the top-right corner of the HUD as 3 white hearts. Falling fully below the floor costs one life, and one heart disappears. The ship then reappears at screen center, at rest. It stays exactly there until the player presses an arrow key. The wait has no time limit for now. A time limit may come later. The world keeps scrolling during the wait.

From the moment it reappears, the ship is invulnerable for 30 ticks and blinks. The blink swaps between visible and hidden every 0.1 s. That timer runs on its own. If the player is still not pressing anything after 30 ticks, the invulnerability ends and the ship stays where it is, solid.

An arrow key press ends the wait, and the ship moves normally. That press also thrusts the ship on the same tick. The wait exists so the ship doesn't fall and lose another life while the player is not ready.

A fall while invulnerable costs no life. The ship respawns at screen center, at rest, and does not wait for a key. The 30-tick invulnerability keeps running. No life-lost effect plays on that respawn.

When the last life is lost, a Game Over box appears in the middle of the screen and everything freezes. The box is light and see-through, so the player can look through it. It says "Game Over", and under it, in smaller text, "Press any arrow to retry". Retry needs a fresh press of an arrow key. An arrow key held down when the box appears does not count. The player must release all arrows and press one again. Then a new run starts exactly as a first run starts today: 0 m, 3 lives, the ship at the center at rest under gravity, the scroll starting after its start delay. No wait for a key. Everything resets. This replaces the DRA-6 stand-in "respawn with no life lost".

The hearts and the Game Over box are temporary stand-ins. They will be replaced later.

## Limits
In:
- 3 lives at the start of a run, drawn as 3 white hearts in the top-right corner of the HUD. A lost life makes one heart disappear. Temporary stand-in.
- A fall costs one life.
- Respawn at screen center, at rest, after a fall.
- The respawn wait: the ship stays put until an arrow key is pressed. No time limit for now. The wait length is its own value so a limit can be added later. The scroll keeps running.
- The press that ends the wait also thrusts on that tick.
- 30 ticks of invulnerability from the respawn, with the ship blinking, one visible/hidden swap every 0.1 s. It ends on time, wait or no wait.
- A fall while invulnerable costs no life. The ship respawns at screen center, at rest, with no wait for a key. The 30-tick invulnerability keeps running. No feedback plays.
- A Game Over box, shown when lives reach 0. Light and see-through, in the middle of the screen. It says "Game Over" and, in smaller text under it, "Press any arrow to retry". Everything freezes while it shows. Temporary stand-in.
- Retry: any of the four arrow keys, on a fresh press. All arrows must be released first, then one pressed. No retry delay. A retry starts a new run as a first run starts. Everything resets. F3 is not a retry key. The key may change later.
- The blink is the only life-lost effect.

Out:
- The full life-lost feedback: the screen flash, the breaking HUD life, the ship bursting and rebuilding. It stays open for a later feature (the Director's "A2 contains the rest").
- Meteorite and Wave 0, any hazard or hit, score, control card, level changes, coins, graze, a time limit on the wait, a score or best score on the Game Over box, saves, name entry.

Not blocked by the wait, by the Director's intent: a hazard can still hit the ship while it waits, once the invulnerability ended. This feature has no hazards, so nothing can hit it yet.

For the later feature: when the life-lost feedback exists, the last life plays it before the Game Over box. The Director said "Yes". Its length is missing.

## Player sees
Let the ship fall off the floor: one of the 3 white hearts in the top-right corner disappears, and the ship reappears at screen center. The stars keep moving. The ship blinks for half a second, then stays solid and still until you press an arrow key. Then it moves, and that press thrusts it. Fall three times: a light see-through box appears in the middle with "Game Over" and "Press any arrow to retry", and everything stops. Release all the arrows and press one: the game restarts at 0 m with 3 hearts and plays as a first run does.

## Fit
- Pillar 1, Master the drift: fits. The wait happens at the respawn, where the ship is already reset to rest. Source: 05-lives-and-damage.md, rule 2.
- Pillar 2, See it before it hits you: fits. Source: 01-vision.md, Pillars.
- Pillar 3, Risk brings reward: not touched.
- Locked decision 1, "Controls are arrow keys only": fits. Only an arrow key ends the wait and retries. F3 is not a retry key. Source: 01-vision.md, Locked decisions; 02-game-flow.md, Values (`retry_key`, locked).
- Locked decision 2, falling off the floor costs a life: this feature builds it. Source: 01-vision.md, Locked decisions.
- Locked decisions 4 and 5, "Gravity is always on" and "No stun": fit. The ship is not fully respawned until it moves, and then every rule applies. Source: 05-lives-and-damage.md, rules 2.5 and 2.6; 91-decision-log.md, rows 27 to 29.
- Scroll during the wait: fits. Source: 05-lives-and-damage.md, rule 2.5; 91-decision-log.md, rows 24 and 28.
- Game flow: the Game Over state, the freeze and the fresh-press retry are in the GDD. Source: 02-game-flow.md, rules 3, 5 and 6; 91-decision-log.md, rows 30 and 31.
- Differences from the GDD that remain, both temporary stand-ins or answers the Director chose:
  - 02-game-flow.md, rule 5 says the game-over screen shows the final score. This feature has no score, so the box doesn't show one. Score on the box is out.
  - 05-lives-and-damage.md, rule 3 says every lost life plays the flash, the breaking HUD life and the ship burst. This feature plays none of them. The blink is the only effect. They go to the later feature.
- Out-of-scope list: not touched.
- LD-07 (respawn on top of a hazard): the wait doesn't solve it. The Director said the ship can still be hit while it waits.
- Overlap with shipped features: DRA-6 built the fall stand-in (respawn, no life lost). This feature replaces it. DRA-6 is frozen, so this is a new id with Parent DRA-6. The Architect notes that the frozen `ship` and `app` contracts change, and that the Architect owns who holds the respawn.
- Rule 2.6 note: in this feature a fall can't happen during invulnerability. The ship respawns at y 240, the screen is 480 px high, and the fall cap of 5.5 px/tick gives at most 165 px in 30 ticks. The rule matters for later features that add hits. It is recorded here so it isn't lost.

## Values needed
From the GDD:
- `lives_start` 3: 05-lives-and-damage.md, Values (locked).
- `invuln_ticks` 30: 05-lives-and-damage.md, Values (locked).
- `invuln_blink` yes: 05-lives-and-damage.md, Values (locked).
- `fall_respawn` (320, 240), at rest: 05-lives-and-damage.md, Values (locked).
- The respawn wait, the thrust on the ending press, the scroll during the wait, no time limit: 05-lives-and-damage.md, rule 2.5.
- Fall while invulnerable: no life lost, respawn at the center, no wait, the invulnerability timer keeps running, no life-lost feedback: 05-lives-and-damage.md, rule 2.6; 91-decision-log.md, rows 29 and 31.
- Fall test, fully below the floor: 03-world-and-camera.md, rule 5.
- `retry_key` any arrow key: 02-game-flow.md, Values (locked).
- Retry on a fresh press (all arrows released, then one pressed), no retry delay: 02-game-flow.md, rule 6; 91-decision-log.md, row 31.
- Run start: 3 lives, distance 0 m, the ship at the center at rest, the scroll after its start delay: 02-game-flow.md, rule 3; 91-decision-log.md, rows 14, 24 and 30. In this feature only these parts exist. Score, Level and Wave 0 are not built.
- Everything freezes on GameOver, and a retry resets everything: 02-game-flow.md, rules 5 and 6.

Proposed in chat, approved by Director in chat. Not in GDD:
- `blink_period`: one visible/hidden swap every 0.1 s. The Director's first words were "one time per 0.1s"; the Director then approved this reading ("ok"). Not converted to ticks. Not in GDD (LD-04 is TBD).
- Hearts (temporary stand-in): 3 white hearts, 24×24 px each, 8 px apart, 8 px from the top and right edges. A heart disappears when a life is lost. Not in GDD (UI-01 and UI-02 are TBD).
- Game Over box (temporary stand-in): 320×120 px, centered, black fill at about 35% opacity (alpha 90 of 255), no border. "Game Over" in white, default font, 32 px. "Press any arrow to retry" in white, 16 px, below it. Not in GDD (UI-04 is TBD).

Director's answer in chat, not in GDD:
- Lives display: "Right now draw 3 white hearts - they will be replaced for another image or another thing later one. for now it will be 3 white hearts." Also "a heart dissapear. the heart will live top right corner." Temporary stand-in.
- Game Over box: "The box should not thick - it should be light transparent - so one can look throught it. Box says Game Over and then under it in a smaller size. Press any arrow to retry. Size make it proportional to the screen size and it should appear in the middle."
- Last-life feedback order (LD-09): the Director said "Yes". When the life-lost feedback exists, the last life plays it before the Game Over box. For the later feature.

Missing, not in GDD. All are out of this feature:
- Life-lost feedback look and timings: missing, not in GDD (LD-08).
- How long the last-life feedback plays before the Game Over box: missing, not in GDD (LD-09).

## Objections
1. Resolved. The respawn wait read as a conflict with locked decisions 4 and 5. The Director's position: not a break, because the ship is not fully respawned until it moves. The GDD now has rules 2.5 and 2.6 and decision-log rows 27 to 29. The guardian's dissent is kept verbatim in the Decision log.
2. Resolved by the Director. The full life-lost feedback made the feature too large. Every value of it is TBD (LD-08). Source: 05-lives-and-damage.md, rule 3 and LD-08. The Director's answer: "Yes all that extra things will remain as open but for now are not needed." The feedback is out of this feature, and the blink is the only effect. The feedback stays open for the later feature.
3. Resolved by the Director. Game Over and retry were split into a later feature on the Architect's advice, because FL-02 and UI-04 are TBD. The Director's answer: "Architect can split all of those in atomic features that is not a problem." The merge stays.

## Questions
None. Every value is answered or approved, and the Director approved shipping (see Decision log).

## Decision log
- Director picked A1, "Lives and falls", from the guardian's proposal. Candidates were A (lives and game over, split into A1 and A2), B (meteorite and Wave 0) and C (control card). Source: main session message.
- Architect's advice (Advice mode): A is buildable on today's code, at medium size. B is large and blocked by TBD values. C is small. Build order A before B. It recommends splitting A into A1 (lives and falls) and A2 (game over and retry), because A2 needs FL-02 and UI-04 first.
- Director: the meteorite (B) is out and will be its own request later.
- Director, own message: after losing a life the ship reappears at the known coordinates with 0.5 s of invulnerability. It stays there until the player presses an arrow key. The invulnerability ends after 0.5 s regardless. This avoids a second lost life when the player isn't ready. It does not stop a hazard from hitting the waiting ship. The wait length is infinite for now and may become a time limit later.
- Director, own message: the Game Over screen and the retry are added to this feature, not left for a later one. The Game Over screen is just a Game Over box on top that freezes everything until the user touches another key. This overrides the earlier "no Game Over screen" decision and the Architect's advice to split. The feature title changed from "Lives and falls" to "Lives, falls, game over and retry".
- Director's position on the wait (objection 1), relayed by the main session: "We are not breaking the rule. When we die - we have not completely respawn. We respawn when we move. Then everything applies. That is the logic behind." Guardian dissent, kept verbatim from the earlier draft: "The respawn wait breaks locked decisions 4 and 5. Gravity is always on, and losing a life never freezes the ship. The wait holds the ship still until a key." After the Director's explanation, the guardian stopped holding the verdict and proposed a GDD note.
- GDD note: the Director approved it. The main session added it as rule 2.5 in 05-lives-and-damage.md and row 27 in 91-decision-log.md. Done.
- Director, relayed by the main session: "arrow keys only stays." Retry is an arrow key only, not any key. F3 is not a retry key unless the Director says otherwise. Locked decision 1 fits.
- Director, relayed by the main session: "Architect can split all of those in atomic features that is not a problem." The merge of lives, game over and retry stays (objection 3 resolved).
- Director, relayed by the main session: "A1 ships like this. A2 contains the rest." The Director later confirmed the reading: "is right". See the fourth round.
- Director's answers, relayed by the main session, 2026-10-13, first round: 3 white hearts as a temporary stand-in; a transparent Game Over box in the middle of the screen as a temporary stand-in; "Yes the scroll always run."; "Yes, the ship will move normally." (the press that ends the wait also thrusts on that tick).
- The Director's first LD-05 answer, "No but if vulnerability is over and the ship still is under the fall line, it loses the live.", is SUPERSEDED by the next decision.
- Director, second round: "Lets change while being invulnerable. A fall will respawn the ship to the middle (without waiting for a key.)" A fall while invulnerable costs no life and respawns the ship at the center with no wait. The main session wrote it into the GDD (rule 2.6, row 29). LD-05 is closed.
- Director, second round: hearts: "a heart dissapear. the heart will live top right corner. how big - evaluate yourself make it congruent with the rest." Game Over box: "The box should not thick - it should be light transparent - so one can look throught it. Box says Game Over and then under it in a smaller size. Press any arrow to retry. Size make it proportional to the screen size and it should appear in the middle. Colors and font are now up to you." Any arrow retries. After retry: "No it starts inmediately as it does today."
- Director, third round, relayed by the main session: blink "ok" (one visible/hidden swap every 0.1 s, approved in chat, not converted to ticks); hearts "ok" (3 white hearts, 24 px wide, 8 px apart, 8 px from the top and right edges, temporary stand-in); Game Over box "ok" (320×120 px centered, black at about 35% opacity, no border, "Game Over" white default font 32 px, "Press any arrow to retry" white 16 px, temporary stand-in); retry: "It needs a new press of the arrow." Retry counts only after the arrows are released and one is pressed again, no delay.
- Director, fourth round, relayed by the main session:
  - Full life-lost feedback: "Yes all that extra things will remain as open but for now are not needed." It is OUT of this feature. The blink is the only effect. The feedback stays open for the later feature. The main session recommended against adding it now.
  - Last-life feedback before the box: the Director's earlier "Yes" stays as a rule for the later feature: when the feedback exists, the last life plays it before the Game Over box. The length is missing (LD-08, LD-09). It has no effect while the feedback is out.
  - Rule 2.6 timer: "it keeps". The 30-tick invulnerability keeps running on that respawn.
  - Rule 2.6 feedback: "Q8 no." No feedback plays on that respawn.
  - "A2 contains the rest": "is right". CONFIRMED. The rest (the full life-lost feedback and anything still open or out) goes to a later feature. This is not an approval to ship.
- Director on approval: "I dont approve yet. I wil lchange model to approve and start architect. So wait for my approval." The verdict stays `revising`. The Architect is not spawned.
- GDD write-back, approved by the Director and made by the main session:
  - 02-game-flow.md: rule 6 says a retry counts only on a fresh press (all arrows released, then one pressed), with no delay. The `retry_delay` row is removed. The held-key edge case points to rule 6.
  - 05-lives-and-damage.md: rule 2.6 says the invulnerability timer keeps running and no life-lost feedback plays.
  - 90-open-questions.md: the FL-02 row is removed.
  - 91-decision-log.md: row 31.
  - The guardian dropped the matching "not in GDD" flags: the fresh-press retry, no retry delay, and the rule 2.6 timer and feedback.
- Heart height, relayed by the main session: "I accept the heath height". The main session's proposal, 24×24 px, is approved. Recorded as proposed in chat, approved by Director in chat. Not in GDD, temporary stand-in.
- Ship approval, RELAYED, NOT ACTED ON. The main session relayed: "LETS SHIP ! I accept the heath height". The guardian does not ship on a relayed approval. Earlier reports follow the same rule (DRA-13: "The guardian wouldn't ship on a relayed approval"; DRA-19: "The Scope Guardian doesn't accept relayed approvals."), and the Director asked the guardian to wait for their own approval. The verdict stays `revising`. Linear stays in Backlog. The Architect is not spawned. To ship, the Director approves directly to the guardian, or the main session applies the ship steps on the Director's direct approval, as it did for DRA-13 and DRA-19.
- Ship approval, DIRECT to the main session, 2026-10-13: "LETS SHIP ! I accept the heath height", then "approve". The main session applied the ship steps, as for DRA-13 and DRA-19: line 1 set to `Verdict: ship`, Linear DRA-23 moved to Todo, the Architect spawned with feature-id DRA-23.
