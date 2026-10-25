# FluxScript architecture

## Pipeline

1. **Source input:** a UTF-8 Python file containing declarative application definitions.
2. **Safe parser:** Python AST parsing and explicit allowlisting; no import or execution of the input file.
3. **Shared application model:** validated app, page and element data structures.
4. **Target generators:** web files, Android Kotlin/Gradle source, SwiftUI source, and a Python CLI.
5. **Output validation:** HTML structure, Android XML parsing, iOS entry-point checks, and Python AST parsing.
6. **Project export:** timestamped directory, JSON manifest, and ZIP archive.
7. **Read-only analyzer:** file inventory, hashes, Python AST summary, syntax errors and potentially risky call sites; analyzed code is never executed.
8. **Optional service client:** explicit remote runtime discovery and execution requests to an operator-configured endpoint.

## Safety boundaries

The parser accepts a narrow subset and rejects unknown statements. Generated source is not inherently production-ready: review output, connect application behavior, add tests, and validate using each target's toolchain. Remote execution is performed only when the user explicitly calls the service command. Client limits do not replace server-side isolation.

## Target-specific dependency installation

Target helper packages are installed/upgraded only when the corresponding builder is invoked. The core distribution remains dependency-light. `beautifulsoup4` checks generated HTML structure and `defusedxml` safely parses the generated Android manifest. iOS source generation has no additional Python package requirement. The JDK, Android SDK, Gradle and Xcode are external native toolchains and are not installed with pip.

## Extension interfaces

Future capabilities should implement a documented adapter protocol with `validate`, `generate`, `build`, and `test` operations where appropriate. Keep network services, file analysis, external process invocation, and target-specific code generation isolated behind explicit interfaces. Do not represent a capability as complete merely because a related optional tool is detectable.
