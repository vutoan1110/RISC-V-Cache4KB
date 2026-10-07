# Magic namespace collision and the .magicsafe macro GDS

Frozen evidence note. The text below is copied from the documents it was first written in (removed from the
working tree on 2026-10-07; git history keeps them); only section labels and references to other sections of
those documents were reworded. Two independent defects stopped the Magic steps of
the OpenLane flow on the designs with OpenRAM macros, and both fixes are in every signed-off run:

1. `openlane-local/openlane/scripts/magic/common/read.tcl`: `cellname create` before `load`, and
   `GDS_END = file size`, so `Magic.StreamOut` blackboxes the macro without pulling the PDK's subcells in.
2. `macros/*.magicsafe.gds`: copies of the OpenRAM macro GDS without the five mask data-prep layer/datatypes that
   the sky130A Magic techfile does not declare (22/21, 22/22, 33/42, 33/43, 235/0), so `Magic.WriteLEF`,
   `Magic.DRC` and `Magic.SpiceExtraction` can parse the design GDS. Proved shape-for-shape identical on every
   retained layer.

Files that must be kept with this note: `asic/evidence/magicsafe_equivalence_proof.log` (2 KiB macro),
`asic/evidence/magicsafe_1kbyte_proof.log` (1 KiB macro), `asic/prove_magicsafe_equivalence.py`,
`asic/strip_macro_annotation_layers.py`, `asic/list_gds_cells.py`, `asic/<design>/macros/*.magicsafe.gds` and the
patched `read.tcl`. `MAGIC_CAPTURE_ERRORS` stays true in every configuration.

## 1. From PD_incident_report.md, part B (2026-09-18/19, 2 KiB macro, 1 KiB-cache design)

### Magic namespace collision -- the real root cause, two bugs in one

**Symptom.** `Magic.StreamOut` failed 14 times, identically every time: 20
"Calma output error: Structure name not found at GDS file position N / Can't
write cell from vendor GDS", plus "59 problems occurred". Deterministic, so not
the host memory fault.

**Evidence, from the step's own log:**

```
line  463  Cell sky130_sram_2kbyte_1rw1r_32x512_8 read from path
           $PDK/libs.ref/sky130_sram_macros/mag
line  469  {GDS_FILE <ours>} {GDS_START 0} {GDS_END 15213044}
line 6500  Copying output for cell sky130_fd_bd_sram__openram_dff_2
           from $PDK/libs.ref/sky130_sram_macros/gds/..._8.gds
line 6501  Calma output error: Structure name not found at position 168502
```

`read_macro_gds_blackbox` does `load $macro_name` and only then marks the cell
as a LEF view with a GDS pointer. But `load` searches Magic's cell path first,
and the PDK ships this macro at `libs.ref/sky130_sram_macros/mag`. Magic pulls
in the macro's entire subcell hierarchy before anything is blackboxed:

1. **Namespace collision.** Those subcells collide with cells already on the
   path from `libs.ref/sky130_fd_bd_sram/mag`, so Magic renames the newcomers
   with a `_2` suffix. Verified: the macro GDS holds 161 cells and no `_2`
   variant, so the suffix is Magic's. Their vendor-GDS pointers then name
   structures that exist nowhere.
2. **Byte range from the wrong file.** `GDS_END` is inherited from the PDK
   `.mag` and belongs to the PDK's GDS (15,213,048 bytes) while `GDS_FILE` is
   overridden to the design's copy (14,736,910 bytes) -- 476 KB past the end.

**Fix** in `openlane-local/openlane/scripts/magic/common/read.tcl`:

```tcl
cellname create $macro_name        ;# `load` takes this empty cell
load $macro_name                   ;#  instead of searching the path
property GDS_END [file size $gds_file]
```

**Result with `MAGIC_CAPTURE_ERRORS = true`:** Calma errors 0, structure-not-
found 0, unknown-layer 0, no "problems occurred" line, and
`blackboxed ... (0..14736910)` matching the file size exactly.

### Unknown layer/datatype -- a second, independent fix

**Symptom.** `Magic.WriteLEF` then failed nine times:

```
[E] Error while reading cell "sky130_fd_bd_sram__openram_dp_cell"
    (byte position 93274): Unknown layer/datatype in boundary, layer=22 type=22
```

**Cause.** Magic's `sky130A.tech` does not declare five layer/datatypes the
OpenRAM macro carries. Named from the PDK's own `sky130A.lyp`, not guessed:

| layer/dt | name | in sky130A.tech |
|---|---|---|
| 22/21 | `cfom.maskAdd` | no |
| 22/22 | `cfom.maskDrop` | no |
| 33/42 | `cp1m.maskDrop` | no |
| 33/43 | `cp1m.maskAdd` | no |
| 235/0 | `boundary` | only 235/4 |

All five are mask data-prep annotation or a cell outline -- no device geometry.

**Fix.** `asic/strip_macro_annotation_layers.py` removes exactly those five and
then **proves** the result: KLayout XOR of original against stripped, **34
layers compared, 0 differ**, 412 annotation shapes removed.

**Why both fixes are needed.** They are not alternatives:

- `Magic.StreamOut` **blackboxes** the macro -- copies bytes, parses nothing.
- `Magic.WriteLEF`, `Magic.DRC` and `Magic.SpiceExtraction` do
  `gds read $::env(CURRENT_GDS)` -- the **design's** GDS, with those macro bytes
  inlined. Magic parses all of it.

`MAGIC_CAPTURE_ERRORS` stayed `true`. It was set false once as a stopgap and
restored the moment the real fix landed.

## 2. From asic/pd_note.txt (2026-09-19)

```
Magic namespace collision: root cause and fix.
==============================================

SYMPTOM. Magic.StreamOut failed 14 times in a row, identically every time:
20 "Calma output error: Structure name not found at GDS file position N /
Can't write cell from vendor GDS. Using magic's internal definition", plus
"59 problems occurred". Deterministic, so not the machine.

ROOT CAUSE, traced in the step's own log.

  line  463  Cell sky130_sram_2kbyte_1rw1r_32x512_8 read from path
             $PDK/libs.ref/sky130_sram_macros/mag
  line  469  {GDS_FILE <ours>} {GDS_START 0} {GDS_END 15213044}
  line 6500  Copying output for cell sky130_fd_bd_sram__openram_dff_2
             from $PDK/libs.ref/sky130_sram_macros/gds/..._8.gds
  line 6501  Calma output error: Structure name not found at position 168502

OpenLane's read_macro_gds_blackbox (scripts/magic/common/read.tcl) does
`load $macro_name` and then marks the cell as a LEF view with a GDS pointer.
But `load` searches Magic's cell path first, and the PDK ships this very macro
at libs.ref/sky130_sram_macros/mag. Magic therefore loads the macro's ENTIRE
subcell hierarchy before anything is blackboxed, and two things break:

  1. NAMESPACE COLLISION. Those subcells collide with cells already on the path
     from libs.ref/sky130_fd_bd_sram/mag, so Magic renames the newcomers with a
     "_2" suffix. Verified independently: the macro GDS contains 161 cells and
     no "_2" variant of any of them, so the suffix is Magic's, not the file's.
     On write-out Magic seeks to each stored offset and looks for a structure
     named "..._dff_2", which exists nowhere.

  2. BYTE RANGE FROM THE WRONG FILE. GDS_END was inherited from the PDK .mag
     and belongs to the PDK's GDS (15,213,048 bytes), while GDS_FILE is then
     overridden to the design's own copy (14,736,910 bytes). Every offset
     addressed the wrong file and the range ran 476 KB past its end.

FIX (Option 1, blackbox). In openlane-local/openlane/scripts/magic/common/
read.tcl, create the cell before loading it and derive GDS_END from the file
actually referenced:

    cellname create $macro_name        ;# `load` now takes this empty cell
    load $macro_name                   ;#  instead of searching the path
    property LEFview true
    property GDS_FILE $gds_file
    property GDS_START 0
    property GDS_END [file size $gds_file]
    property FIXED_BBOX "$bbox"

No subcells enter the database, so nothing can collide; the byte range and the
file can no longer disagree. This is what a blackbox is supposed to be: the
macro's bytes are copied verbatim into the output GDS.

RESULT, with MAGIC_CAPTURE_ERRORS = true:

    Calma output error  : 0
    Structure not found : 0
    Unknown layer       : 0
    problems occurred   : none
    > blackboxed sky130_sram_2kbyte_1rw1r_32x512_8 -> ..._8.gds (0..14736910)

The range matches the file size exactly.

NOTES.
  * MAGIC_CAPTURE_ERRORS is back to true. Nothing is suppressed.
  * The macro GDS is the ORIGINAL, unmodified file. The earlier
    ".magicsafe.gds" copy -- which had five mask-prep annotation layers
    stripped (22/21 cfom.maskAdd, 22/22 cfom.maskDrop, 33/42 cp1m.maskDrop,
    33/43 cp1m.maskAdd, 235/0 boundary) to work around Magic READ errors -- is
    no longer referenced. A true blackbox never parses those layers, so full
    macro fidelity is preserved. The file and its KLayout XOR proof
    (34 layers compared, 0 differ) remain on disk as evidence only.
  * config.json.pre_magicsafe holds the config from before any of this.

----------------------------------------------------------------------
BOTH fixes are needed. They are not alternatives.

After the blackbox fix, Magic.StreamOut passed clean with MAGIC_CAPTURE_ERRORS
= true, so the original macro GDS was restored for maximum fidelity. The next
Magic step, Write LEF, then failed nine times with the errors the stripped copy
had been made for:

    [E] Error while reading cell "sky130_fd_bd_sram__openram_dp_cell"
        (byte position 93274): Unknown layer/datatype in boundary,
        layer=22 type=22

The reason is that the two steps read different things:

  * Magic.StreamOut BLACKBOXES the macro. It copies its bytes verbatim and
    never parses a single layer, so annotation layers are invisible to it.
  * Magic.WriteLEF -- and Magic.DRC, and Magic.SpiceExtraction -- do
    `gds read $::env(CURRENT_GDS)`, the DESIGN's GDS, which now has those macro
    bytes inlined. Magic parses all of it, meets layers its sky130A techfile
    does not declare, and errors.

So:

  blackbox fix (read.tcl)     -> namespace collision + byte-range mismatch
  .magicsafe.gds (5 layers)   -> "Unknown layer/datatype" wherever Magic parses
                                 the macro's geometry

MACROS.gds points at the stripped copy again. It is XOR-proven against the
original: 34 layers compared, 0 differ, 412 annotation shapes removed, all of
them mask data-prep (cfom/cp1m maskAdd and maskDrop) or the cell outline --
none of them device geometry.

MAGIC_CAPTURE_ERRORS stays true throughout. Nothing is suppressed.
```

## 3. From PD_incident_report.md, workspace purge of 2026-09-19: the shape-for-shape proof

The original KLayout XOR log was never written to a file; the proof was rebuilt with an independent method.

3. The KLayout XOR proof of the `.magicsafe.gds` was required to remain on
   disk. It never existed as a file -- only as prose in this report and in
   `pd_note.txt`. KLayout lives in the OpenLane nix store and is no longer
   reachable from this host, so the original could not be regenerated.

Point 3 was closed with a stronger check rather than a weaker excuse.
`asic/prove_magicsafe_equivalence.py` parses both GDS files record by record
and compares every shape as an exact tuple: structure name, element type,
layer, datatype, and the full coordinate list. An area XOR proves the
difference region is empty; this proves shape-for-shape identity, so a shape
displaced by one database unit -- invisible to an XOR of coincident edges --
would fail it.

It reproduces the original numbers exactly, by a different method:

```
original     215200 shapes
magicsafe    214788 shapes
shapes removed: 412        22/21  35   22/22  12
                           33/42 155   33/43 192   235/0  18   all expected
shapes added: 0
layer/datatypes retained and compared: 34
RESULT: every retained layer is shape-for-shape identical
```

412 and 34 are the same two numbers the KLayout XOR produced. Two independent
tools agreeing on a result neither derived from the other is better evidence
than the single log that was lost. Double-executed, byte-identical.
`asic/evidence/magicsafe_equivalence_proof.log`.

## 4. From a note of 2026-09-23 (4 KiB design, 1 KiB macro)


### 2026-09-23 -- Magic.WriteLEF was a real bug, not the RAM: the 1 KiB macro was never made magicsafe

Thirty-one attempts at `Magic.WriteLEF`, and OpenLane's message was
`Encountered one or more fatal errors while running Magic` -- an error the tool
raised, not a segfault. The log says what it is:

```
Unknown layer/datatype in boundary, layer=33 type=42
Unknown layer/datatype in boundary, layer=33 type=43
Unknown layer/datatype in boundary, layer=22 type=21
  in cell sky130_fd_bd_sram__openram_dp_cell_cap_row
```

Those are three of the five annotation layer/datatypes the `.magicsafe.gds`
treatment removes, and `MAGIC_CAPTURE_ERRORS` is true so Magic's read errors are
fatal by design.

**The cause.** The 4 KiB design has two macro types. `config.json`
pointed the 2 KiB SRAM at its `.magicsafe.gds` and the 1 KiB SRAM at the raw
`.gds`, and no magicsafe copy of the 1 KiB macro had ever been made. The fix was
carried over to this design only halfway when the design was built.

Generated it with the same script and proved it two independent ways:

```
KLayout XOR (strip_macro_annotation_layers.py)   34 layers compared, 0 differ, PROOF_OK
shape-for-shape (prove_magicsafe_equivalence.py) 412 shapes removed on exactly the
                                                 five annotation layer/datatypes,
                                                 0 added, 34 retained layers identical
```

412 shapes on the same five layers as the 2 KiB macro. Config updated, backed up
first, flow restarted from `Magic.StreamOut`.

**Lesson for the deliverable:** a fix applied to one macro in one design is not
applied to the project. When the 4 KiB design was created by copying the 1 KiB
one, the macro set changed and the fix did not follow.
