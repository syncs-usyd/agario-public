# Agar Bot Battle Rules

## Arena

- The game takes place in a square arena.
- Players are spawned in each corner of the arena.
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
their blobs, clamped so the vision square remains inside the arena bounds.

Players can observe:

- Their own authoritative blob list with absolute coordinates, sizes, and cooldowns
- Food within their current vision square
- Viruses whose circles intersect their current vision square
- Other blobs whose circles intersect their current vision square, with absolute coordinates and size

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

- A blob may eat an enemy blob only if it is at least 20% larger.
- The smaller blob's center must lie inside the larger blob's radius.
- When a blob is eaten, the larger blob absorbs its size contribution.
- A player is eliminated only when all of their blobs have been eaten.

## Viruses

- Viruses are stationary green spiky objects scattered around the arena.
- The arena maintains a fixed virus count (default 3).
- Viruses have a fixed radius (default 1.5).
- A blob can only consume a virus if its mass is at least 20% larger than the virus's mass.
- The virus's center must lie inside the blob's radius.
- When a blob consumes a virus:
  - The virus's mass is added to the blob.
  - The blob is forcibly split into multiple pieces (up to the maximum blob count of 16).
  - Each resulting piece has a merge cooldown.
- Consumed viruses respawn at random positions to maintain the virus count.
- Viruses are visible to players when any part of the virus enters their vision square.

## End Condition

The game ends when either:

- Only one player remains alive
- The configured round limit is reached

The winner is the highest-ranked remaining player by alive state and final size.
