# Agar Bot Battle Rules

## Arena

- The game takes place in a square arena.
- The arena size and player count are controlled by config values.
- Food is spawned randomly and maintained at a fixed count.

## Player State

Each player controls one or more circular blobs with:

- Absolute `x, y` position for each blob
- Radius for each blob
- Alive/dead state
- Per-blob merge cooldown after splitting

## Vision

Each player has a single square view centered on the mass-weighted centroid of
their blobs.

Players can observe:

- Their own authoritative blob list with absolute coordinates, sizes, and cooldowns
- Food within their current vision square
- Other visible blobs with absolute coordinates and size

The vision size is recalculated by the engine each turn as a function of the
sum of the player's blob radii.

## Turns

On each round, every living player submits a movement direction and may optionally request a split.

Supported direction formats:

- A vector using `x` and `y`
- An angle in `degrees`

The engine normalizes the direction and applies movement using the configured base speed. Larger players move more slowly according to a size-based speed factor.

## Splitting And Merging

- A blob may split only if its mass is at least the configured split threshold.
- Mass is proportional to area, so splitting conserves `radius^2`.
- When a split happens, the new blob is ejected in the submitted movement direction with a configured launch speed.
- Split blobs cannot merge until their cooldown expires.
- Blobs owned by the same player are kept non-overlapping by the engine at all times.
- Same-player blobs are gently pulled together over time, and merge automatically once they are both off cooldown and touching.

## Eating Food

- Food is eaten when it lies inside any owned blob's radius.
- Eating food increases that blob's size.
- After food is consumed, the engine respawns food until the configured food count is restored.

## Eating Players

- A blob may eat an enemy blob only if it is at least 10% larger.
- The smaller blob's center must lie inside the larger blob's radius.
- When a blob is eaten, the larger blob absorbs its size contribution.
- A player is eliminated only when all of their blobs have been eaten.

## End Condition

The game ends when either:

- Only one player remains alive
- The configured round limit is reached

The winner is the highest-ranked remaining player by alive state and final size.
