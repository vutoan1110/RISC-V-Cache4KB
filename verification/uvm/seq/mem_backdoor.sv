// Backdoor program loader. The memory image is a plain class array, so the
// program is written straight into it before reset is released; no bus
// transaction is needed and the DUT never sees the load.
class mem_backdoor extends uvm_object;

    `uvm_object_utils(mem_backdoor)

    function new(string name = "mem_backdoor");
        super.new(name);
    endfunction

    // Returns the number of words written. Fatals if the image cannot be read,
    // because every downstream check would otherwise be meaningless.
    static function int unsigned load(native_mem_model mem, string path,
                                      string ctx = "mem_backdoor");
        int words = mem.load_hex(path);
        if (words == -1)
            `uvm_fatal(ctx, $sformatf("cannot open program image '%s'", path))
        if (words == -2)
            `uvm_fatal(ctx, $sformatf("program image '%s' is larger than the %0d-byte memory model",
                                      path, mem.size_bytes))
        if (words == 0)
            `uvm_fatal(ctx, $sformatf("program image '%s' is empty", path))
        `uvm_info(ctx, $sformatf("loaded %0d words from %s", words, path), UVM_LOW)
        return int'(words);
    endfunction

endclass
