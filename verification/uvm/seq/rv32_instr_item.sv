// One randomly chosen instruction slot for the program generator.
//
// The constraints keep every generated program inside the claimed subset:
// RV32I computational + Zmmul, no system instruction, no fence, no ecall, no
// trap. x28..x31 are reserved for the generator's own scaffolding, data
// accesses stay inside the data window, and sub-word accesses stay aligned
// because the core does not implement misaligned access.
class rv32_instr_item extends uvm_object;

    typedef enum bit [3:0] {
        KIND_R,        // register ALU
        KIND_I,        // immediate ALU
        KIND_MUL,      // Zmmul
        KIND_LOAD,
        KIND_STORE,
        KIND_BRANCH,   // always forward, so the program makes progress
        KIND_JAL,
        KIND_JALR,
        KIND_UPPER     // LUI / AUIPC
    } kind_e;

    rand kind_e     kind;
    rand bit [4:0]  rd;
    rand bit [4:0]  rs1;
    rand bit [4:0]  rs2;
    rand bit [2:0]  funct3;
    rand bit        alt;        // funct7 = 0100000, i.e. SUB / SRA / SRAI
    rand bit [11:0] imm;
    rand bit [4:0]  shamt;
    rand bit [19:0] uimm;
    rand bit [8:0]  data_off;   // byte offset from the data base register
    rand bit        upper_is_auipc;

    // Set by the generator before randomize().
    int unsigned data_bytes = 256;
    bit          allow_branch = 1;   // cleared when the tail is too short
    bit          allow_jal    = 1;
    bit          allow_jalr   = 1;

    `uvm_object_utils(rv32_instr_item)

    function new(string name = "rv32_instr_item");
        super.new(name);
    endfunction

    // Only x1..x27 are writable; the generator owns x28..x31.
    constraint c_regs {
        rd  inside {[1:27]};
        rs1 inside {[1:27]};
        rs2 inside {[1:27]};
    }

    // Same mix as verification/random/gen_rv32.py, which the retained random
    // differential record was produced with.
    constraint c_kind {
        kind dist {
            KIND_R      := 20,
            KIND_I      := 20,
            KIND_MUL    := 12,
            KIND_LOAD   := 10,
            KIND_STORE  := 10,
            KIND_BRANCH := 12,
            KIND_JAL    := 6,
            KIND_JALR   := 4,
            KIND_UPPER  := 6
        };
    }

    constraint c_room {
        (!allow_branch) -> (kind != KIND_BRANCH);
        (!allow_jal)    -> (kind != KIND_JAL);
        (!allow_jalr)   -> (kind != KIND_JALR);
    }

    constraint c_funct3 {
        (kind == KIND_MUL)    -> funct3 inside {3'b000, 3'b001, 3'b010, 3'b011};
        (kind == KIND_LOAD)   -> funct3 inside {3'b000, 3'b001, 3'b010, 3'b100, 3'b101};
        (kind == KIND_STORE)  -> funct3 inside {3'b000, 3'b001, 3'b010};
        (kind == KIND_BRANCH) -> funct3 inside {3'b000, 3'b001, 3'b100, 3'b101, 3'b110, 3'b111};
    }

    // Data accesses stay in the window and stay naturally aligned.
    constraint c_data_off {
        data_off < data_bytes;
        (kind == KIND_LOAD) -> {
            (funct3 inside {3'b001, 3'b101}) -> (data_off[0] == 1'b0);
            (funct3 == 3'b010)               -> (data_off[1:0] == 2'b00);
        }
        (kind == KIND_STORE) -> {
            (funct3 == 3'b001) -> (data_off[0] == 1'b0);
            (funct3 == 3'b010) -> (data_off[1:0] == 2'b00);
        }
    }

    // SUB and SRA are the only funct7=0100000 encodings in RV32I.
    constraint c_alt {
        (kind == KIND_R) -> (alt -> funct3 inside {3'b000, 3'b101});
        (kind == KIND_I) -> (alt -> funct3 == 3'b101);
        (kind inside {KIND_MUL, KIND_LOAD, KIND_STORE, KIND_BRANCH,
                      KIND_JAL, KIND_JALR, KIND_UPPER}) -> (alt == 1'b0);
    }

endclass
