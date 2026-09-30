# Copyright 2022 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


proc read_pdk_gds {} {
    set old_rescale [gds rescale]
    set old_readonly [gds readonly]
    gds rescale false
    gds readonly true
    set gds_files_in $::env(CELL_GDS)
    foreach gds_file $gds_files_in {
        puts "> gds read $gds_file"
        gds read $gds_file
    }
    gds rescale $old_rescale
    gds readonly $old_readonly
}

proc read_tech_lef {} {
    puts "> lef read $::env(TECH_LEF)"
    lef read $::env(TECH_LEF)
}

proc read_macro_lef {} {
    if { [info exist ::env(MACRO_LEFS)] } {
        foreach lef_file $::env(MACRO_LEFS) {
            puts "> lef read $lef_file"
            lef read $lef_file
        }
    }
}

proc read_extra_lef {} {
    if { [info exist ::env(EXTRA_LEFS)] } {
        foreach lef_file $::env(EXTRA_LEFS) {
            puts "> lef read $lef_file"
            lef read $lef_file
        }
    }
}

proc read_extra_gds {} {
    set old_rescale [gds rescale]
    set old_readonly [gds readonly]
    gds rescale false
    gds readonly true
    if {  [info exist ::env(EXTRA_GDS_FILES)] } {
        set gds_files_in $::env(EXTRA_GDS_FILES)
        foreach gds_file $gds_files_in {
            puts "> gds read $gds_file"
            gds read $gds_file
        }
    }
    gds rescale $old_rescale
    gds readonly $old_readonly
}

proc read_macro_gds_blackbox {} {
    if { [info exists ::env(__MACRO_GDS)] } {
        foreach macro $::env(__MACRO_GDS) {
            set macro_name [lindex $macro 0]
            set gds_file [lindex $macro 1]
            set bbox [lindex $macro 2]
            # `load` searches Magic's cell path. For a macro the PDK also ships
            # -- here sky130_sram_macros/mag -- it finds that .mag and pulls the
            # macro's entire subcell hierarchy into the database, each subcell
            # carrying byte-offset pointers into the PDK's own GDS. Two things
            # then break, and both surface as
            #   "Calma output error: Structure name not found at GDS file
            #    position N / Can't write cell from vendor GDS":
            #
            #  1. those subcells collide by name with cells already on the path
            #     (sky130_fd_bd_sram/mag), so Magic renames the newcomers with a
            #     "_2" suffix -- verified: the macro GDS holds 161 cells and no
            #     "_2" variant, so the suffix is Magic's -- and their pointers
            #     then name structures that exist nowhere under that name;
            #  2. GDS_END is inherited from the PDK file (15,213,048 bytes)
            #     while GDS_FILE is overridden below to the design's own copy
            #     (14,707,182 bytes), so every offset addresses the wrong file
            #     and the tail runs past its end.
            #
            # Creating the cell first makes `load` take that empty definition
            # instead of searching the path. No subcells, no inherited
            # pointers -- which is what a blackbox is supposed to be. GDS_END is
            # then set from the file actually referenced, so the byte range and
            # the file always agree.
            cellname create $macro_name
            load $macro_name
            property LEFview true
            property GDS_FILE $gds_file
            property GDS_START 0
            property GDS_END [file size $gds_file]
            property FIXED_BBOX "$bbox"
            puts "[property]"
            puts "> blackboxed $macro_name -> $gds_file (0..[file size $gds_file])"
        }
    }
}

proc read_macro_gds {} {
    if { [info exist ::env(MACRO_GDS_FILES)] } {
        set gds_files_in $::env(MACRO_GDS_FILES)
        foreach gds_file $gds_files_in {
            puts "> gds read $gds_file"
            gds read $gds_file
        }
    }
}

proc read_pdk_lef {} {
    foreach lef_file $::env(CELL_LEFS) {
        puts "> lef read $lef_file"
        lef read $lef_file
    }
}

proc read_def {} {
    set def_read_args [list]
    lappend def_read_args $::env(CURRENT_DEF)
    if { $::env(MAGIC_DEF_NO_BLOCKAGES) } {
        lappend def_read_args -noblockage
    }
    if { $::env(MAGIC_DEF_LABELS) } {
        lappend def_read_args -labels
    }
    puts "> def read $def_read_args"
    def read {*}$def_read_args
}
