<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-0-check-qt-project-setup' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0 — Check Qt Project Setup

**Always call the AskUserQuestion tool** — even if a project appears to be open. Never assume the currently open project is the intended target.

Before calling, read the context to personalise the question:
- If a project is already open (files visible, `CMakeLists.txt` present), name it in the first option so the user can confirm or redirect.
- If the user's request is an **update** ("update my colors", "re-extract tokens", "sync the design system"), omit the "create new project" option — updates always target an existing project.

**For an update request** — two options, no "create new":
```
tool: AskUserQuestion
question: "Which project should I update the design tokens in?"
options:
  - "This project — <detected project name or path> (currently open)"
  - "A different existing project — I'll give you the path"
```

**For an initial setup request** — all three options:
```
tool: AskUserQuestion
question: "Which Qt project should I set up the design system in?"
options:
  - "This project — <detected project name or path> (currently open)"
  - "A different existing project — I'll give you the path"
  - "Create a new project"
```

If no project is open yet, replace the first option with just `"An existing project — I'll give you the path"`.

**If the project exists (confirmed or path provided):** Note the project path. Continue to Step 1 — do not ask for Figma files yet.

**If a new project is needed:** Scaffold the folder structure and create `main.cpp` and `main.qml` now, then continue to Step 1:

```
my-project/
├── CMakeLists.txt      ← set up in Step 7
├── main.cpp            ← create now (template below)
├── main.qml            ← create now (template below)
└── design-system/      ← generated files go here
```

Create `main.cpp` with this exact content — use `QGuiApplication`, **not** `QApplication` (Widgets is not needed for Qt Quick):

```cpp
#include <QGuiApplication>
#include <QQmlApplicationEngine>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QQmlApplicationEngine engine;

    engine.loadFromModule("<ProjectName>", "Main");

    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}
```

Replace `<ProjectName>` with the URI used in `qt_add_qml_module()` — they must match exactly.

> **Do not use the old `QUrl url(u"qrc:/..."_qs)` pattern.** In Qt 6, `qt_add_qml_module` places files under `qrc:/qt/qml/<URI>/` — not `qrc:/<URI>/` as in Qt 5. Using the old path causes a silent load failure. `loadFromModule()` avoids this entirely and is the correct approach for Qt 6.5+.

Create `Main.qml` as a placeholder — **capital M, not lowercase**. `loadFromModule()` is case-sensitive and looks for a type named `Main`, which maps to `Main.qml`:

```qml
import QtQuick

Window {
    width:   640
    height:  480
    visible: true
    title:   "My Qt App"
}
```

> **CMake setup:** The full CMakeLists.txt — including singleton registration — is written in Step 7 once all QML files are known. Do not write it now. If the user encounters any build configuration issues, suggest the user check Qt's CMake documentation at https://doc.qt.io/qt-6/cmake-get-started.html rather than troubleshooting inline.

---
