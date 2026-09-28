<!-- Moved verbatim from qt-qml-profiler/SKILL.md, the
     'references' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## References

- [qml-performance-anti-patterns.md](references/qml-performance-anti-patterns.md) —
  event-type-keyed catalogue of common QML performance anti-patterns
  (Binding, Javascript, HandlingSignal, Creating, Compiling,
  SceneGraph/Painting, Memory/PixmapCache) with symptoms, causes, and
  fixes. Load this when mapping a hotspot to a root cause in Step 5.
- [scripts/parse-qmlprofiler-trace.py](references/scripts/parse-qmlprofiler-trace.py) —
  `.qtd` trace parser that emits the JSON summary consumed in Step 4.

Each file below is loaded on demand, not at triage. 1 file(s):

- `references/qml-performance-anti-patterns.md` — QML Performance Anti-Pattern Reference. Use this reference when analyzing hotspots from a qmlprofiler trace.
