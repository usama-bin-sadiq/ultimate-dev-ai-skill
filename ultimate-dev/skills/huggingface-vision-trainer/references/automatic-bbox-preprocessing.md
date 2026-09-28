<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'automatic-bbox-preprocessing' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Automatic Bbox Preprocessing

The object detection training script (`scripts/object_detection_training.py`) automatically handles bbox format detection (xyxy→xywh conversion), bbox sanitization, `image_id` generation, string category→integer remapping, and dataset truncation. **No manual preprocessing needed** — just ensure the dataset has `objects.bbox` and `objects.category` columns.
