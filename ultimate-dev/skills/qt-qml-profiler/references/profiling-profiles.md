<!-- Moved verbatim from qt-qml-profiler/SKILL.md, the
     'profiling-profiles' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Profiling Profiles

When `--profile` is not specified, default to `full`.

| Profile | qmlprofiler --include value |
|---|---|
| `full` | *(omit --include, records everything)* |
| `rendering` | `scenegraph,animations,painting,pixmapcache` |
| `logic` | `javascript,binding,handlingsignal,compiling,creating` |
| `memory` | `memory,creating` |
