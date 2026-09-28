<!-- Moved verbatim from slack-gif-creator/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Helper Utilities

These are optional helpers for common needs. **Use, modify, or replace these with custom implementations as needed.**

### GIF Builder (Assembly & Optimization)

```python
from core.gif_builder import GIFBuilder

# Create builder with your chosen settings
builder = GIFBuilder(width=480, height=480, fps=20)

# Add frames (however you created them)
for frame in my_frames:
    builder.add_frame(frame)

# Save with optimization
builder.save('output.gif',
             num_colors=128,
             optimize_for_emoji=False)
```

Key features:
- Automatic color quantization
- Duplicate frame removal
- Size warnings for Slack limits
- Emoji mode (aggressive optimization)

### Text Rendering

For small GIFs like emojis, text readability is challenging. A common solution involves adding outlines:

```python
from core.typography import draw_text_with_outline, TYPOGRAPHY_SCALE

# Text with outline (helps readability)
draw_text_with_outline(
    frame, "BONK!",
    position=(240, 100),
    font_size=TYPOGRAPHY_SCALE['h1'],  # 60px
    text_color=(255, 68, 68),
    outline_color=(0, 0, 0),
    outline_width=4,
    centered=True
)
```

To implement custom text rendering, use PIL's `ImageDraw.text()` which works fine for larger GIFs.

### Color Management

Professional-looking GIFs often use cohesive color palettes:

```python
from core.color_palettes import get_palette

# Get a pre-made palette
palette = get_palette('vibrant')  # or 'pastel', 'dark', 'neon', 'professional'

bg_color = palette['background']
text_color = palette['primary']
accent_color = palette['accent']
```

To work with colors directly, use RGB tuples - whatever works for the use case.

### Visual Effects

Optional effects for impact moments:

```python
from core.visual_effects import ParticleSystem, create_impact_flash, create_shockwave_rings

# Particle system
particles = ParticleSystem()
particles.emit_sparkles(x=240, y=200, count=15)
particles.emit_confetti(x=240, y=200, count=20)

# Update and render each frame
particles.update()
particles.render(frame)

# Flash effect
frame = create_impact_flash(frame, position=(240, 200), radius=100)

# Shockwave rings
frame = create_shockwave_rings(frame, position=(240, 200), radii=[30, 60, 90])
```

### Easing Functions

Smooth motion uses easing instead of linear interpolation:

```python
from core.easing import interpolate

# Object falling (accelerates)
y = interpolate(start=0, end=400, t=progress, easing='ease_in')

# Object landing (decelerates)
y = interpolate(start=0, end=400, t=progress, easing='ease_out')

# Bouncing
y = interpolate(start=0, end=400, t=progress, easing='bounce_out')

# Overshoot (elastic)
scale = interpolate(start=0.5, end=1.0, t=progress, easing='elastic_out')
```

Available easings: `linear`, `ease_in`, `ease_out`, `ease_in_out`, `bounce_out`, `elastic_out`, `back_out` (overshoot), and more in `core/easing.py`.

### Frame Composition

Basic drawing utilities if you need them:

```python
from core.frame_composer import (
    create_gradient_background,  # Gradient backgrounds
    draw_emoji_enhanced,         # Emoji with optional shadow
    draw_circle_with_shadow,     # Shapes with depth
    draw_star                    # 5-pointed stars
)

# Gradient background
frame = create_gradient_background(480, 480, top_color, bottom_color)

# Emoji with shadow
draw_emoji_enhanced(frame, '🎉', position=(200, 200), size=80, shadow=True)
```
