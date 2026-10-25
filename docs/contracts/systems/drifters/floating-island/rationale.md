# Drifters, the floating island, rationale
Part of: drifters
Read when: you ask why the floating island is built the way it is.

## Rationale

- **The island's sizes and `arm` are even whole px (DRA-86).** The view draws at the rounded center, so with even sizes every box edge and triangle corner is a whole px from it, and the drawn pixels are exactly the shape's pixels. That is what lets the edge stay inside the hitbox to the pixel.
- **A variant is a shape kind and a size (DRA-86).** 05-floating-islands.md says a new shape or size is a new variant. The size is data; the box is the rectangle kind at 120 × 120. A new shape kind needs a new `IslandShape` and its case in `island_hitbox`, which is a new look, so a code change is right there.
- **`invert` is refused on the rectangle and the box (DRA-86).** Rule 9 lists `invert` for the L, the T and the triangle only. The shape table's "the same" for the rectangle says a flipped rectangle would look no different, so a placement that sets it is a mistake, refused as the other drifters refuse what they lack. Decided by Architect, Director to confirm.

- **The island's look is pre-rendered (DRA-86).** A 320 × 120 shape drawn row by row, or two boxes and two insets, every frame for every island would cost far more than one blit. The image depends only on its key, which never changes in an island's life, so it is built once.
- **The edge is the shape less its inset (DRA-86).** Outlining each box would draw a line across the L's and the T's joint, inside the island. Filling the whole shape in the edge color and then the inset shapes in the fill color draws the edge along the outer sides only, and never outside the shape.
- **Colors and the 2 px edge stay in the view (DRA-86).** As for every drifter so far (DRA-47 and DRA-62 Rationale): colors are placeholder look values, and a wider edge changes nothing but the look. Every size and the `arm`, which decide where the ship stops, are in the tuning file.
- **No art task (DRA-86).** Final art and sound are out of scope (scope report DRA-86, Out). The look is a placeholder drawn in code.
