# Custom PDN config for soc_with_sram, based verbatim on OpenLane2's own
# default template (nix store: openlane/scripts/openroad/common/pdn_cfg.tcl)
# with ONE addition: an explicit add_pdn_ring on the macro grid, on the
# SAME layers (met3+met4) as the sky130_sram_2kbyte_1rw1r_32x512_8 macro's
# own SHAPE ABUTMENT vccd1/vssd1 ring (see macros/lef/*.lef: the macro's
# ring runs met4 verticals at x=[4.76,6.5]/[676.6,678.34] and met3
# horizontals at y=[4.76,6.5]/[410.04,411.78], all relative to the macro's
# own origin). The default template only ever draws stdcell-grid stripes
# on met4(vertical)/met5(horizontal) and only calls add_pdn_connect (never
# add_pdn_ring) for the macro grid -- met3 is never touched at all by the
# stock flow, and the default 10-unit macro halo pushes met4 stdcell
# stripes away from the macro besides. This is the root cause of the
# persistent "not connected to any power/ground nets" / SIGSEGV chain
# from the prior session's runs 3-13.
#
# STATUS: written from LEF geometry + OpenROAD pdn.tcl command reference,
# NOT YET RUN. The add_pdn_ring core_offset/width/spacing values below are
# a first, reasoned attempt (small offset so the new ring lands close to
# where the macro's own ring already is) -- expect to need at least one
# more iteration once real tool output is seen, exactly like every other
# fix in this flow so far.

source $::env(SCRIPTS_DIR)/openroad/common/set_global_connections.tcl
set_global_connections

set secondary []
foreach vdd $::env(VDD_NETS) gnd $::env(GND_NETS) {
    if { $vdd != $::env(VDD_NET)} {
        lappend secondary $vdd
        set db_net [[ord::get_db_block] findNet $vdd]
        if {$db_net == "NULL"} {
            set net [odb::dbNet_create [ord::get_db_block] $vdd]
            $net setSpecial
            $net setSigType "POWER"
        }
    }
    if { $gnd != $::env(GND_NET)} {
        lappend secondary $gnd
        set db_net [[ord::get_db_block] findNet $gnd]
        if {$db_net == "NULL"} {
            set net [odb::dbNet_create [ord::get_db_block] $gnd]
            $net setSpecial
            $net setSigType "GROUND"
        }
    }
}

set_voltage_domain -name CORE -power $::env(VDD_NET) -ground $::env(GND_NET) \
    -secondary_power $secondary

# --- stdcell grid: unchanged from the default template ---
define_pdn_grid \
    -name stdcell_grid \
    -starts_with POWER \
    -voltage_domain CORE \
    -pins "$::env(FP_PDN_VERTICAL_LAYER) $::env(FP_PDN_HORIZONTAL_LAYER)"

add_pdn_stripe \
    -grid stdcell_grid \
    -layer $::env(FP_PDN_VERTICAL_LAYER) \
    -width $::env(FP_PDN_VWIDTH) \
    -pitch $::env(FP_PDN_VPITCH) \
    -offset $::env(FP_PDN_VOFFSET) \
    -spacing $::env(FP_PDN_VSPACING) \
    -starts_with POWER -extend_to_core_ring

add_pdn_stripe \
    -grid stdcell_grid \
    -layer $::env(FP_PDN_HORIZONTAL_LAYER) \
    -width $::env(FP_PDN_HWIDTH) \
    -pitch $::env(FP_PDN_HPITCH) \
    -offset $::env(FP_PDN_HOFFSET) \
    -spacing $::env(FP_PDN_HSPACING) \
    -starts_with POWER -extend_to_core_ring

add_pdn_connect \
    -grid stdcell_grid \
    -layers "$::env(FP_PDN_VERTICAL_LAYER) $::env(FP_PDN_HORIZONTAL_LAYER)"

if { $::env(FP_PDN_ENABLE_RAILS) == 1 } {
    add_pdn_stripe \
        -grid stdcell_grid \
        -layer $::env(FP_PDN_RAIL_LAYER) \
        -width $::env(FP_PDN_RAIL_WIDTH) \
        -followpins \
        -starts_with POWER

    add_pdn_connect \
        -grid stdcell_grid \
        -layers "$::env(FP_PDN_RAIL_LAYER) $::env(FP_PDN_VERTICAL_LAYER)"
}

if { $::env(FP_PDN_CORE_RING) == 1 } {
    add_pdn_ring \
        -grid stdcell_grid \
        -layers "$::env(FP_PDN_VERTICAL_LAYER) $::env(FP_PDN_HORIZONTAL_LAYER)" \
        -widths "$::env(FP_PDN_CORE_RING_VWIDTH) $::env(FP_PDN_CORE_RING_HWIDTH)" \
        -spacings "$::env(FP_PDN_CORE_RING_VSPACING) $::env(FP_PDN_CORE_RING_HSPACING)" \
        -core_offset "$::env(FP_PDN_CORE_RING_VOFFSET) $::env(FP_PDN_CORE_RING_HOFFSET)"
}

# --- macro grid: THIS is the actual fix ---
# Zero halo (default template uses FP_PDN_*_HALO = 10, which keeps every
# stdcell-grid stripe at least 10 um away from any macro -- too far to
# ever reach the abutment ring sitting only 1.36-6.5 um inside the
# macro's own boundary).
define_pdn_grid \
    -macro \
    -default \
    -name sram_macro_grid \
    -starts_with POWER \
    -halo "0 0"

# Explicit ring on met3+met4, matching the layers the macro's own
# vccd1/vssd1 abutment ring uses. A small core_offset (measured outward
# from each macro instance's own bounding box) is used so the new ring's
# inner edge lands at/near the macro boundary, close enough to the
# macro's own ring (inset 1.36-6.5 um) for OpenROAD's connectivity pass
# to merge/via them.
#
# UPDATE (after debug_skip_3): the original "2.0/2.0" width/spacing here
# (a first, hand-guessed value loosely mirroring the macro's own ring
# width) made pdngen auto-generate a non-standard via3 array that violates
# real sky130A DRC rules -- confirmed via full-flow KLayout DRC: 1128
# errors, 100% under via3.1/via3.1_a/via3.2 (min via3 width/spacing
# 0.2um each, per sky130A_mr.drc:711-715), 0 errors on any other rule.
# Switched to $FP_PDN_VWIDTH/$FP_PDN_VSPACING (3.1um each) -- the same
# width already used, DRC-clean, by this design's real stdcell_grid
# stripes -- instead of an arbitrary new value, on the reasoning that
# pdngen's via-array generator is already proven not to violate via
# rules at that width elsewhere in this exact design.
add_pdn_ring \
    -grid sram_macro_grid \
    -layers "$::env(FP_PDN_VERTICAL_LAYER) met3" \
    -widths "$::env(FP_PDN_VWIDTH) $::env(FP_PDN_VWIDTH)" \
    -spacings "$::env(FP_PDN_VSPACING) $::env(FP_PDN_VSPACING)" \
    -core_offset "1.0 1.0"

# UPDATE (after run18b): the ring-width fix above made ZERO difference --
# run18b (width 3.1um, spacing 1.7um -- confirmed via resolved.json) hit
# the EXACT same 1128 violations, same 768/288/72 category split, as the
# original 2.0/2.0 attempt. Checked the violation coordinates directly
# against this macro's own LEF: they land at e.g. x=678 relative to the
# macro's own origin (macro at x=150 -> absolute x=828, matching multiple
# reported violations) -- squarely inside the macro's OWN vccd1 abutment
# strip on met4 (LEF: `RECT 676.6 4.76 678.34 411.78`, only 1.74um wide).
# The ring's declared width/spacing only governs the metal shape MY ring
# draws -- it does not control the via3 CUT ARRAY pdngen auto-generates
# wherever that ring/connect geometry overlaps the macro's own (fixed,
# LEF-defined, un-editable) 1.74um-wide abutment strip. pdngen's default
# via-array packer tries to fit multiple via3 cuts into that narrow
# overlap and produces cuts/spacing below the 0.2um sky130A minimum
# regardless of the ring's own width. Real fix: constrain the via ARRAY
# itself (not the ring shape) via add_pdn_connect's own -max_rows/
# -max_columns (confirmed available: `openroad -exit ... <<< "help
# add_pdn_connect"`) to force a single via3 cut per connection point
# instead of letting pdngen auto-pack an array that doesn't fit this
# specific 1.74um-wide strip.

add_pdn_connect \
    -grid sram_macro_grid \
    -layers "met3 $::env(FP_PDN_VERTICAL_LAYER)" \
    -max_rows 1 -max_columns 1

add_pdn_connect \
    -grid sram_macro_grid \
    -layers "$::env(FP_PDN_VERTICAL_LAYER) $::env(FP_PDN_HORIZONTAL_LAYER)"
