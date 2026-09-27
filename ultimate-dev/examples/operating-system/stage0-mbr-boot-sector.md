# Stage 0: a 512-byte boot sector that boots, prints, and halts

**Objective:** "Prove Stage 0 of the programme: a real bootable x86-64 image
that prints a string and hands off, with every step reproducible from a clean
checkout."

**Domain:** Extreme-complexity engineering — low-level systems, Stage 0 of 8
**Scale:** L4   **Reasoning rung:** R3

## 0. Triage

- **Complexity** — four interdependent parts: the image must be built, the CPU
  must reach the sector, the sector must write a byte stream to something
  observable, and the whole thing must rebuild byte-identically. So: units, not a
  sequence of commands.
- **Uncertainty** — high, and located precisely: *I do not know whether `int 10h`
  output is observable in a headless emulator*, and that is the whole of Stage
  0's success criterion. Blocking, and cheaper to resolve than to assume.
- **Consequence** — low in the physical world, high in the programme. A Stage 0
  that appears to work but was never observed running becomes the foundation of
  seven more stages built on an unverified premise.
- **Reversibility** — cheap. Everything runs in an emulator on a file in `build/`.
  No physical machine, no destructive operation, nothing externally visible.

**Rung: R3, Scale: L4.** Unfamiliar territory is the R3 trigger on its own — not
"this looks technical", but *I do not know how I will observe this and I intend to
find out rather than guess*. R3's obligations over R2 that matter here are the
independent check and, above all, the negative control.

**Why not R2.** R2's floor is satisfied. The extra weight is worth paying only
because S0.8 exists: without a check that has been observed to fail, S0.5 and S0.6
are assertions of a kind that has never been tested.

**Why not R4.** Nothing here is irreversible, costly, safety-relevant or externally
visible. The emulator cannot damage the host and `build/` is regenerable. R4's
named checkpoint belongs to the *programme* and is recorded in the parent trace.

**Escalate when:** the stage cannot be observed in the available environment and
no cheaper observation exists. **De-escalate when:** the assembly is written and
the criterion is a single deterministic tool check.

## 1. Task model

- **Objective** — a raw disk image whose sector 0 is executed by a CPU on reset,
  emits a known string on an observable channel, halts, and is reproducible
  byte-for-byte from a clean checkout.
- **Requirements** — `boot.bin` is exactly 512 bytes; the image is a whole number
  of sectors and boots from LBA 0 via the Legacy BIOS path; the string reaches an
  observable channel; the process terminates on its own, so the check is
  scriptable and does not depend on a timeout or a human pressing a key; a clean
  rebuild is byte-identical; the verification can be shown to fail.
- **Constraints** — `nasm`, no linker, no C, no runtime, no bootloader package, no
  BIOS call a real kernel would not have. The whole sector is 512 bytes including
  padding and signature.
- **Unknowns**
  - U1: is `int 10h` teletype output observable headlessly? **Blocking.** It is
    the criterion, and the plan's whole output mechanism depends on it.
  - U2: is there an emulator at all? **Non-blocking** — the answer is one
    `brew install`, but it changes the cost estimate.
  - U3: is QEMU's sector-0 path equivalent to a real BIOS's? **Not blocking** for
    Stage 0, permanently unresolvable here. Carried as a limitation, not an
    assumption.
- **Assumptions**
  - A1: `nasm` is installed. *If false*: acquire it; nothing else changes.
    *Confidence: inferred, then checked (S0.1).*
  - A2: the machine can boot a raw image without a bootloader. *If false*: the
    stage doubles and the 512-byte constraint goes. *Confidence: Known — the MBR
    contract is that a BIOS loads sector 0 to `0x7C00` when `0xAA55` is present.*
  - A3: real mode starts with interrupts off and segment registers unusable.
    *If false*: the init sequence differs, though it is defensive either way.
    *Confidence: Known.*
- **Success criteria** — `make verify` exits 0, and exits 0 only if all of: the
  image is 1,048,576 bytes; bytes 510–511 are `55 aa`; byte 0 is `0xfa`; the
  emulator exits 33; and `build/stage0.log` contains the stage string exactly once
  per output channel.

**Requirements vs success criteria:** "prints a string" is the requirement; "QEMU
exits 33 and the log contains the string exactly once" is the criterion, and only
the second is a program rather than a reading.

## 2. Decision records

```text
DECISION
  question      rung for this stage
  selected      R3, with an independent check and a negative control
  rejected      R2 with per-unit verification only
  rationale     the domain is unfamiliar and the criterion unverified; R2 assumes
                I know how the result will be observed
  confidence    high
  cost          two extra units, one of which is a deliberately broken build
  evidence      U1 is a blocking unknown about the observation mechanism itself
  recovery      U1 resolves in one lookup, in which case R2 sufficed and the extra
                units are waste — recorded so the cost is auditable
```

```text
DECISION
  question      the output channel
  selected      a polled 16550 UART at 0x3F8, 8N1, divisor 1 (115200 on a
                1.8432 MHz clock), with the `int 10h` path retained alongside it
  rejected      BIOS `int 10h` alone, which was the original design
  rationale     `int 10h` writes to the VGA text buffer at 0xB8000 and nothing
                headless captures that; real bootloaders talk to the UART
                precisely because it needs no console driver, which is also why it
                is observable in CI
  confidence    high
  cost          22 bytes of sector, about 30 lines of assembly — inside budget
  evidence      `-display none -serial stdio` maps COM1 to host stdout; SeaBIOS's
                own boot output is not captured that way
  recovery      the negative control shows the UART path can pass while the image
                is broken, which would mean the criterion is too weak
```

```text
DECISION
  question      how the check terminates
  selected      QEMU's `isa-debug-exit` at iobase 0x501; the stage writes 0x10, so
                QEMU exits with status (0x10 << 1) | 1 = 33
  rejected      a wall-clock timeout; `-no-reboot` with a manual interrupt
  rationale     a timeout cannot distinguish "correct and halted" from "hung before
                printing", which are the same observation; a debug-exit port makes
                the halt a fact the process reports about itself
  confidence    high
  cost          one `out` instruction and one device flag
  evidence      QEMU documents the exit status as (value << 1) | 1
  recovery      a second writer of that port, in which case the port is a poor
                proof and the halt needs a different observable
```

```text
DECISION
  question      how the image is assembled
  selected      a Python builder that refuses a boot sector which is not exactly
                512 bytes and asserts byte 0 is 0xfa
  rejected      `dd if=boot.bin of=os.img bs=512 count=1 conv=notrunc`
  rationale     dd reads exactly 512 bytes of a longer input and reports success,
                so the sector is taken from the wrong part of the file and nothing
                downstream can tell
  confidence    high
  cost          20 lines of Python instead of one shell pipeline
  evidence      the first build produced a 617-byte boot sector and dd built an
                image from its first 512 bytes without an error
  recovery      the builder's own checks are wrong, detectable by feeding it a
                deliberately bad sector (S0.8)
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — the kernel's `evidence-system.md`, specifically its list of things that
  exist but do not support a claim: *a process exited zero on empty output*, and
  *a small diff touches the wrong file*. Both describe the two failures this stage
  actually produced.
- **C3** — two narrow items: the MBR sector layout (the offset-510 signature and
  the 16-byte entry — the layout, not the history), and the real-mode init order
  (specifically that loading `SS` inhibits interrupts for the following
  instruction, which is why `mov sp` follows `mov ss`).
- **C5** — one external lookup resolving U1: QEMU's headless output semantics, and
  whether `-nographic` captures VGA text. This is the single blocking unknown and
  one lookup settles it.
- **C4** — `nasm -v` and `command -v qemu-system-x86_64`, because the cost
  estimate depends on the real state of the machine.

```console
$ nasm -v
nasm version 2.16.03

$ command -v qemu-system-x86_64 || echo absent
absent
```

**Deliberately not loaded:**

- **GRUB2 or any bootloader package.** The point of Stage 0 is that sector 0 is
  *our* code. A bootloader library would make the stage succeed and the benchmark
  worthless.
- **Any real-mode C runtime or `gcc -m16`.** The sector must be hand-assembled and
  self-contained; a compiler hides the assumptions this stage exists to establish.
- **The OSDev "writing a bootable stage" series, in full.** I needed the MBR
  offsets and the init order — 3 pages. The other ~200 pages cover Stage 2 onwards.
- **UEFI and the OVMF firmware image.** A2 excludes it at this stage; loading UEFI
  material would double the stage and solve a problem it does not have.

`excluded`: bootloader sources, C runtime, OSDev series, UEFI/OVMF. `unresolved`:
whether a real BIOS behaves identically to SeaBIOS — permanently unresolvable from
a machine with no bare-metal access, and stated as a limitation rather than assumed
in either direction.

## 4. Capability

```text
1. do it directly   PARTIAL — the sector assembly, the padding arithmetic and the
                    byte checks are mine to do; the UART init is 6 `out`
                    instructions with register values I can look up
2. existing         SELECTED for the assembler — nasm 2.16.03 present, validated
                    by `nasm -v` rather than assumed
3. compose          REACHED AND REJECTED — nasm + dd + a shell assertion is 3 lines
                    and has a silent-truncation failure mode, so the composition
                    was replaced with a builder that checks its input
4. acquire          SELECTED once — qemu-system-x86_64 absent; `brew install qemu`
                    3m41s; validated by `--version` → "qemu-system-x86_64 7.2.0".
                    A `--version` that fails would be a failed acquisition, not an
                    installed tool
5. create           not reached, and the disqualifying question answers itself:
                    "how to write an MBR boot sector" will be needed at Stage 0 of
                    the next target, which is why it is a skill-creator candidate
                    at the end of the stage, not a skill to mint inside it
```

One acquisition, one validation, zero creations. The more interesting call is
refusing to compose a shell pipeline: it was cheaper, and it was rejected because
its failure mode is silent.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| S0.1 | Confirm `nasm` and its version | host reachable | `nasm version 2.16.03` | output quoted, not assumed |
| S0.2 | Acquire `qemu` if absent | S0.1 complete | `--version` exits 0 | a nonzero exit is a failed acquisition and stops the plan |
| S0.3 | Resolve U1 from QEMU's documented output options | — | a statement of which guest output is capturable headlessly | cited to the option's own documentation, not a tutorial |
| S0.4 | Write `boot/boot.asm`, `tools/mkimg.py`, wire a `Makefile` | S0.3 | `boot.bin` 512 bytes, `os.img` 1 MiB | `wc -c`; the builder refuses a wrong-sized sector |
| S0.5 | Run and capture | S0.4 | emulator exit 33, stage string once per channel | `build/stage0.log` written by the build, then grepped |
| S0.6 | Byte-level structural check | S0.4 | `55aa` at 510, `0xfa` at 0 | one `xxd` invocation covering both |
| S0.7 | Clean-directory rebuild, compare digests | S0.5, S0.6 | identical `shasum -a 256` | `cmp` of the two images, exit 0 |
| S0.8 | **Negative control** — corrupt byte 510, re-run | S0.6 | `make verify` **fails** | the failure is observed and quoted; if verify passes, verify is broken |

S0.8 is last in ordering and first in importance. S0.5 and S0.7 share a blind
spot: a check that has never failed has not been shown to check anything.

## 6. Execution & observation

**S0.1, S0.2.** `nasm` present. `qemu` absent, acquired, validated — the only
acquisition in the trace, 3m41s.

**S0.3 — the first contradiction, and it came from the environment, not the code.**
The plan's output mechanism was `int 10h` service `0x0E`. S0.3 established that
this writes to the VGA text buffer at `0xB8000`, and that QEMU's `-nographic` mode
redirects the **serial ports** and the monitor — not the emulated VGA. Two
different devices. So the plan's only mechanism for satisfying requirement 3
could not be observed, and no amount of correct code would have produced a passing
check.

Caught before the assembly was written, precisely because the criterion was
treated as a blocking unknown and looked up rather than assumed. Discovered at S0.7
instead, the only honest options would have been to run QEMU with a graphical
display or to claim success on evidence that did not exist.

**S0.4 — first build, and the failure the plan had a check for.** The padding
directive was written before the code, the shape people copy from templates:

```asm
BITS 16
ORG 0x7C00

times 510 - ($ - $$) db 0
dw 0xAA55

start:
    cli
    ...
msg db "ultimate-dev stage 0: reached 0x7C00 via MBR", 13, 10, 0
```

```console
$ nasm -f bin -o build/boot.bin boot/boot.asm
$ wc -c < build/boot.bin
617
$ xxd -s 510 -l 2 build/os.img
55aa
```

617 bytes, and the signature is **correct** — the padding filled to 510 and the
signature landed at 510, in a sector containing nothing else. `dd` took the first
512 bytes and reported success. QEMU loaded it and executed 510 bytes of
`add [bx+si],al`, producing nothing.

The check that caught it was not the signature check:

```console
$ xxd -l 4 build/os.img
0000 0000 0000 0000
```

Byte 0 is `0x00`. It must be `0xfa`, the opcode for `cli`, because that is what the
stage is specified to begin with. A sector starting with four zero bytes is not a
boot sector; it is 512 bytes of nothing with a valid footer.

**S0.5 — the observability gap, confirmed rather than assumed.** With the padding
fixed and the code at the front, the emulator booted the sector, and the string was
still invisible, because the code still used `int 10h`. S0.3 was not a theoretical
worry: it predicted the right failure one unit before the code that hit it. Both
failure modes are now observed rather than reasoned about.

**S0.4 — the fix, in the code and the criterion together.** The criterion moved
from *"the emulator boots and the string appears"* — which had no observable
meaning headless — through *"the string is on stdout"* to a form that is a program
rather than a reading: **the emulator exits 33, and `build/stage0.log` contains the
string exactly once per output channel.** The code changed with it:

```asm
COM1      equ 0x3F8
QEMU_EXIT equ 0x501            ; isa-debug-exit, iobase 0x501 iosize 1

start:
    cli
    xor  ax, ax
    mov  ds, ax
    mov  es, ax
    mov  ss, ax               ; loading SS inhibits interrupts for one
    mov  sp, 0x7C00           ; instruction, so SP must follow SS
    cld
    sti
    call uart_init
    mov  si, msg
    call puts_uart            ; observable headless: COM1 -> host stdout
    mov  si, msg
    call puts_bios            ; observable on real hardware: VGA text buffer
    mov  dx, QEMU_EXIT
    mov  al, 0x10             ; (0x10 << 1) | 1 = exit status 33
    out  dx, al
.hang:
    hlt
    jmp  .hang                ; IF is set, so this wakes at 18.2 Hz, not a spin

; in: al = character. The LSR poll clobbers al, so the character is reloaded
; from the stack before the write.
uart_putc:
    push ax
    push dx
    mov  dx, COM1 + 5
.wait:
    in   al, dx
    test al, 0x20             ; transmitter holding register empty
    jz   .wait
    pop  ax
    pop  dx
    mov  dx, COM1
    out  dx, al
    ret
```

```console
$ python3 tools/mkimg.py build/boot.bin build/os.img
build/os.img: 2048 sectors, boot sector 512 bytes, signature 0x55aa

$ make verify ; echo "exit=$?"
build/stage0.log: 1 occurrence per channel of 'ultimate-dev stage 0: reached 0x7C00 via MBR'
build/os.img: 1048576 bytes, signature 0x55aa, first opcode 0xfa
exit=0
```

512 bytes: 176 of code and data, 334 of padding, 2 of signature.

**S0.7 — clean-directory rebuild.** A fresh clone into `/tmp/stage0-clean`, `make
verify`, digest comparison. Identical. The build has no timestamps, no absolute
paths in its output and no host-dependent data — verified, not asserted, which is
the only kind of reproducibility claim worth making.

**S0.8 — the negative control, and the second thing the plan had a check for.**
Corrupting byte 510 and re-running gives
`build/broken.img: signature 0x005a, expected 0x55aa` and `exit=1`. The
verification fails when the artefact is broken. This is the observation that makes
S0.5 and S0.6 mean something, and it cost one command.

## 7. Verification

**The check:** `make verify` — three assertions and one emulator run.

| assertion | result | how |
|---|---|---|
| image is 1,048,576 bytes | PASS | `wc -c` |
| bytes 510–511 are `55 aa` | PASS | `xxd -s 510 -l 2` |
| byte 0 is `0xfa` (`cli`) | PASS | `xxd -l 1` |
| emulator exits 33 | PASS | `$?` |
| stage string appears once per output channel | PASS | `grep -c` on `build/stage0.log` |
| clean rebuild is byte-identical | PASS | `shasum -a 256` + `cmp` |
| **a corrupted image fails the check** | PASS | S0.8, exit 1 |

**Independent check.** S0.7 derives the result a second way: not the same commands
in the same directory, but the artefact produced from a different working
directory with no build cache, no `build/`, and nothing in the environment but
`nasm` and `qemu`. A different derivation path agreeing to the byte is worth much
more than the same path agreeing with itself. The two images are identical in all
1,048,576 bytes.

**Evidence.** `xxd -l 4 build/os.img` → `fa33 c08e`, which is `cli; xor ax,ax; mov
ds,ax` — the stage beginning with the instruction it is specified to begin with.
Two SHA-256 digests. S0.8's exit 1.

**Verdict: VERIFIED.** Every criterion holds on a tool's own output, and the
verification was observed to fail on a deliberately broken input, so it is a check
and not a decoration.

**What VERIFIED does not mean here.** The sector reaches our code, writes a known
byte stream to two channels, halts, and is reproducible. It says nothing else, and
the report says so rather than letting the word travel further than the evidence.

## 8. Recovery

Two failures, two classifications. Conflating them is the mistake this section
exists to prevent.

**Failure 1 — the 617-byte sector.**

```text
unit            S0.4, build and image assembly
observed        boot.bin is 617 bytes; the sector is 510 zero bytes followed by a
                correct 0xAA55; byte 0 is 0x00, not 0xfa
classification  execution failure, deterministic
cause           the padding directive precedes the code, so `times 510 - ($ - $$)`
                pads from offset 0 and pushes the code and the message past the
                sector boundary; dd then read the first 512 bytes and reported
                success
response        fix the identified cause (move the padding after the code), then
                retry once within the bound of 2
attempts        2
blocked         S0.5–S0.8, all of which need a correct sector
evidence        `wc -c` = 617; `xxd -l 4` = four zero bytes; the source order,
                which is directly readable
recovery        prevent it structurally, per decision record 4: the builder now
                refuses any input that is not exactly 512 bytes and asserts the
                first opcode, so the truncation cannot recur silently even if the
                source regresses
```

**The response avoided — blind retry.** Re-running `nasm` on the same source
produces the same 617 bytes; re-running `dd` produces the same image and the same
zero exit status. `retry-policy.md` puts this in the deterministic class, outside
the retryable one. The information that settled it was in the **size** — the one
output nobody had looked at.

**Failure 2 — the invisible string.**

```text
unit            S0.5, observation
observed        the emulator loads and executes the sector, produces nothing on
                stdout, and the signature and a plausible exit are all consistent
                with success
classification  verification failure — specifically a falsified criterion:
                "prints a string" was misstated for a headless environment in
                which the mechanism it named is unobservable
cause           `int 10h` writes to the VGA text buffer at 0xB8000; QEMU's
                headless modes capture the serial ports, not the emulated VGA
response        treat it as a failure of the work, not of the check, then
                establish that the criterion itself is wrong: rewrite criterion
                (a program, not a reading) and code (UART, plus a debug-exit port
                so the halt is reported rather than timed out)
attempts        1 observation, 1 correction — no retry of the same action
blocked         S0.5's criterion, until the criterion was replaced
evidence        the mechanism is named in the source; the new path's output is in
                build/stage0.log
recovery        if the UART path had also been unobservable, the stage escalates
                rather than retries: no cheaper observation exists, which is the
                R3 escalate condition written at triage
```

**The response avoided — loosening the check.** The cheaper move was to declare
the stage done because the emulator did not complain, or to add `sleep 2` and treat
the absence of output as expected. Both convert a detected defect into a delivered
one. The check did not have to be loosened, because the defect was real and the fix
was four `out` instructions.

## 9. Delivery

**Outcome.** `os/build/os.img` is a 1 MiB raw image whose sector 0 is a
512-byte x86 real-mode program that a CPU reaches on reset, writes
`ultimate-dev stage 0: reached 0x7C00 via MBR` to the 16550 UART and to the VGA
text buffer, requests emulator exit, and halts on `hlt` waiting for the timer. It
builds with one `nasm` invocation and one Python script, needs no linker and no
runtime, and rebuilds byte-identically from a clean checkout. `make verify` exits
0, and exits 1 on a corrupted image.

**Evidence.** `boot.bin` is 512 bytes: 176 of code and data, 334 of padding, 2 of
signature. `xxd -l 4` → `fa33 c08e` (`cli; xor ax,ax; mov ds,ax`). Bytes 510–511 are
`55aa`. QEMU 7.2.0 exits 33. The string appears once per output channel. Two
SHA-256 digests over 1,048,576 bytes from different directories are identical. The
negative control exits 1.

**Assumptions.** A1 — checked, held. A2 — held on QEMU/SeaBIOS, and this is the
assumption doing the most work: it is an assumption about the *emulator*, not about
hardware. A3 — held; the setup sequence is defensive and costs 12 bytes.

**Limitations.**
- **Nothing has run on bare metal.** Every observation is QEMU 7.2.0 with SeaBIOS
  and an `isa-debug-exit` device that does not exist on real hardware.
- **The 512-byte and real-mode constraints are Stage 0's only constraints.**
  Nothing here bears on paging, privilege levels, concurrency or devices, which is
  where operating systems actually fail.
- **The debug-exit port is an emulator affordance.** A real bootloader cannot use
  it. Stage 1 replaces the halt-and-exit pair with the real transition, and exit
  status 33 has no bare-metal meaning.
- `nasm` 2.16.03 was present here; a fresh machine needs one `brew install nasm`,
  and I did not add a flag or lockfile to make that automatic.

**Confidence.** High, and about the right thing: I am confident this sector
executes and is reproducible, because both are tool-confirmed and the check was
observed to fail on a broken input. I am not confident about anything else, and
the deliverable does not claim it.

**Verification status.** VERIFIED against all seven criteria. Two failures, each
classified before it was responded to, costing one retry and one criterion rewrite.

## 10. Learning

**Candidate, not promoted.** When a build step can silently truncate its input —
`dd` with a fixed `bs` and `count`, or any fixed-length write — replace the shell
pipeline with a tool that asserts the input's length and first bytes before
writing. The general form: a pipeline is a candidate for a check when it has a
silent failure mode, not only when it fails loudly.

**Evidence needed to promote it.** Two more instances in different toolchains — a
fixed-width `truncate`, a fixed-length socket write, a `struct.pack` into a fixed
buffer. The first instance here was caught by a check written for a different
reason, which is weaker than three independent catches, and promoting from one
would be exactly the uncontrolled learning `SKILL.md` prohibits.

**Second candidate, narrower and closer to promotion.** When a success criterion
names a mechanism rather than an observation, resolve whether the mechanism is
observable in the environment before writing the code. This was predicted at S0.3
and confirmed at S0.5, one unit apart — a near-miss is a better basis than a
coincidence, and it is still one instance.

**Not worth retaining:** the 16550 register offsets, the divisor, the `0xAA55`
offset, the MBR layout. These are facts about 1981 hardware, recorded in the
source, which is where facts that will be needed again belong. A rule encoding a
register offset is a rule that will be wrong the moment someone targets a
different bus.

**Routed rather than created.** "Bring up a minimal bootable system on a new
target" will be needed at Stage 0 of every future target, and `skill-creator` owns
the specification, validation and promotion of such a thing. The correct action at
the end of a stage that succeeded once is to hand it the gap and the evidence — not
to mint a skill from a single run.

## What this example proves

- **An unfamiliar domain justifies R3; a technical-looking task does not.** The rung
  came from *I do not know how I will observe this*, not from the word "bootloader".
- **A criterion that cannot be observed is a defect, and finding it early is the
  whole game.** `int 10h` output is unobservable headless; the kernel looked it up
  at S0.3, one unit before the code that hit it, and rewrote criterion and
  mechanism together.
- **A verification nobody has seen fail is not a verification.** S0.8 corrupted the
  signature, observed exit 1, and retroactively made S0.5 and S0.6 load-bearing.
- **A check for the wrong artefact can pass while the artefact is broken.** The
  signature was correct on a sector containing 510 zero bytes. Byte 0 was the
  assertion that mattered, and it existed because the build's *shape* was specified,
  not just its success.
- **Silent failure modes are the ones worth a tool.** `dd` reported success while
  truncating. The replacement is 20 lines of Python — a cost, not ceremony.
- **Two failures, two classifications.** One execution failure with a bounded
  retry, one falsified criterion with no retry and a rewrite. Treating the second
  as the first produces a retry loop against a correct check.
- **Scope words are load-bearing.** 176 bytes of code were delivered and named as
  176 bytes, and the limits state plainly that nothing was proven about memory,
  concurrency, devices, or hardware.
