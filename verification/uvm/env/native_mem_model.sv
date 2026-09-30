// Byte-addressable memory image shared by the instruction and data agents.
// The region decode mirrors hdl/bus/soc_address_decoder.v so an escaped
// address is reported instead of silently aliasing into RAM.

typedef enum bit [1:0] {
    REGION_RAM,
    REGION_MMIO,
    REGION_UNMAPPED
} native_region_e;

class native_mem_model extends uvm_object;

    protected bit [31:0] words[];
    int unsigned         size_bytes;
    int unsigned         loaded_words;

    `uvm_object_utils(native_mem_model)

    function new(string name = "native_mem_model");
        super.new(name);
        set_size(16384);  // R14: SoC RAM, was 8192
    endfunction

    function void set_size(int unsigned bytes);
        size_bytes   = bytes;
        loaded_words = 0;
        words        = new[bytes/4];
        foreach (words[i]) words[i] = 32'h0;
    endfunction

    // 64 KiB cacheable window, four 256-byte APB pages, everything else is
    // unmapped and must answer with rsp_error.
    static function native_region_e decode(bit [31:0] addr);
        if (addr[31:16] == 16'h0000)
            return REGION_RAM;
        if (addr[31:8] inside {24'h40_0000, 24'h40_0001,
                               24'h40_0002, 24'h40_0003})
            return REGION_MMIO;
        return REGION_UNMAPPED;
    endfunction

    // Inside the cacheable window but beyond the modelled physical RAM.
    function bit is_backed(bit [31:0] addr);
        return (decode(addr) == REGION_RAM) && ((addr >> 2) < words.size());
    endfunction

    function bit [31:0] read_word(bit [31:0] addr);
        return is_backed(addr) ? words[addr >> 2] : 32'h0;
    endfunction

    function void write_word(bit [31:0] addr, bit [31:0] data, bit [3:0] strb);
        bit [31:0] merged;
        if (!is_backed(addr))
            return;
        merged = words[addr >> 2];
        if (strb[0]) merged[7:0]   = data[7:0];
        if (strb[1]) merged[15:8]  = data[15:8];
        if (strb[2]) merged[23:16] = data[23:16];
        if (strb[3]) merged[31:24] = data[31:24];
        words[addr >> 2] = merged;
    endfunction

    // Byte helpers, used by the reference model for sub-word accesses.
    function bit [7:0] read_byte(bit [31:0] addr);
        bit [31:0] word = read_word({addr[31:2], 2'b00});
        return word[8*addr[1:0] +: 8];
    endfunction

    function void write_byte(bit [31:0] addr, bit [7:0] data);
        write_word({addr[31:2], 2'b00}, {4{data}}, 4'b0001 << addr[1:0]);
    endfunction

    // Word-by-word comparison against another image of the same size. Returns
    // the number of mismatches and reports the first few.
    function int unsigned compare(input native_mem_model other,
                                  output string first_diff,
                                  input int unsigned max_report = 4);
        int unsigned diffs = 0;
        first_diff = "";
        foreach (words[i]) begin
            bit [31:0] mine  = words[i];
            bit [31:0] their = other.read_word(i << 2);
            if (mine !== their) begin
                diffs++;
                if (diffs <= max_report)
                    first_diff = {first_diff,
                        $sformatf(" [0x%08h] this=0x%08h other=0x%08h;",
                                  i << 2, mine, their)};
            end
        end
        return diffs;
    endfunction

    // One 32-bit hex word per line, the format produced by
    // verification/directed/build_directed.sh. Returns the word count, or -1
    // when the file cannot be opened.
    function int load_hex(string path);
        int          fd;
        int          code;
        int unsigned idx;
        bit [31:0]   value;

        fd = $fopen(path, "r");
        if (fd == 0)
            return -1;

        idx = 0;
        forever begin
            code = $fscanf(fd, "%h", value);
            if (code != 1)
                break;
            if (idx >= words.size()) begin
                $fclose(fd);
                return -2;
            end
            words[idx] = value;
            idx++;
        end
        $fclose(fd);
        loaded_words = idx;
        return int'(idx);
    endfunction

endclass
