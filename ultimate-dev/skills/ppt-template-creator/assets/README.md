# Template assets

## `template.pptx` is not here, and is not supposed to be

This skill's first step is that **you** supply a `.pptx` or `.potx` — a
PowerPoint template with your own layouts, your brand's master, your slide
sizes. There is no correct template to ship: any file that came with the skill
would be a guess at yours, and a skill that silently used it would produce a deck
in someone else's design.

So step 4 of the workflow copies your file in here, and the generated skill then
points at it. If this directory is empty, that is the correct initial state.

The same is true of `logo.png`, `font.ttf` and `slides.pptx` where a skill
references them: those are brand assets belonging to the organisation using the
skill. A skill that ships a placeholder logo teaches the reader to delete it.
