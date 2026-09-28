<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-7-review-fix-qml-and-update-cmakelists-txt' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 7 — Review, Fix QML, and Update CMakeLists.txt

After generating all QML files, run a validation pass — do not skip any of these checks:

**QML validation:**
- Check for any unresolved token markers the generator left behind — flag these to the user and ask how to resolve them
- Verify every property type matches the `references/token-mapping.md` rules
- Confirm `pragma Singleton` and `import QtQuick` are present in every file
- Check that no values are hardcoded that should come from the token file

**CMakeLists.txt — mandatory update:**

Always update `CMakeLists.txt` as part of this step — do not leave it to the user. Open the file, find the `qt_add_qml_module()` block, and ensure all generated design-system files are listed under `QML_FILES` and registered with `set_source_files_properties`. This is the most common cause of singletons not being accessible in QML.

> **Naming rule:** The target name, URI, and `loadFromModule()` call in `main.cpp` must all use the **same** project name string. Use the actual project name from the `project()` CMake call — do not substitute `MyProject` literally.

```cmake
cmake_minimum_required(VERSION 3.16)
project(<ProjectName> VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Version pin must match qt_standard_project_setup REQUIRES below
find_package(Qt6 6.5 REQUIRED COMPONENTS Quick)
qt_standard_project_setup(REQUIRES 6.5)

# MACOSX_BUNDLE is required on macOS — without it, qt_add_qml_module creates
# a directory named <ProjectName>/ which collides with the linker output file
# (EISDIR error). MACOSX_BUNDLE makes the output MyQtApp.app, no collision.
qt_add_executable(<ProjectName> MACOSX_BUNDLE
    main.cpp
)

set_source_files_properties(
    design-system/Primitives.qml
    design-system/Theme.qml
    design-system/Spacing.qml
    design-system/FontInterface.qml
    PROPERTIES QT_QML_SINGLETON_TYPE TRUE
)

qt_add_qml_module(<ProjectName>
    URI <ProjectName>
    VERSION 1.0
    QML_FILES
        Main.qml   # capital M — must match loadFromModule("<ProjectName>", "Main")
        design-system/Primitives.qml
        design-system/Theme.qml
        design-system/Spacing.qml
        design-system/FontInterface.qml
    # NOTE: do NOT add main.cpp here — it belongs only in qt_add_executable()
)

target_link_libraries(<ProjectName> PRIVATE Qt6::Quick)
```

Replace every `<ProjectName>` with the same string — e.g. `MyQtApp` — matching the `project()` call and the `loadFromModule("<ProjectName>", "Main")` call in `main.cpp`.

After updating CMakeLists.txt, confirm with the user that the file has been saved and show them how to use the singletons in `Main.qml`:

```qml
import QtQuick         // Window is part of QtQuick in Qt 6 — do NOT add import QtQuick.Window
import <ProjectName>   // imports all singletons from the module

Window {
    visible: true
    width: 640
    height: 480
    color: Theme.background_default
}
```

> **CMake issues:** If the user has build errors after updating CMakeLists.txt, suggest the user check Qt's CMake documentation at https://doc.qt.io/qt-6/cmake-get-started.html rather than troubleshooting inline.

---
