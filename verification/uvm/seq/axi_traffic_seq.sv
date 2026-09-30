// Refill traffic on one channel, inside a read window.
class refill_seq extends uvm_sequence #(refill_item);

    int unsigned count = 20;
    bit [31:0]   base  = 32'h0000_0000;
    bit [31:0]   span  = 32'h0000_0400;

    `uvm_object_utils(refill_seq)

    function new(string name = "refill_seq");
        super.new(name);
    endfunction

    task body();
        refill_item item;
        repeat (count) begin
            item = refill_item::type_id::create("refill");
            start_item(item);
            if (!item.randomize() with { addr inside {[base : base + span - 16]}; })
                `uvm_fatal("SEQRAND", "refill_item randomization failed")
            finish_item(item);
        end
    endtask

endclass

// Write-through traffic inside a write window. Requests are issued back to
// back so both entries of the posted-write buffer get used.
class wthru_seq extends uvm_sequence #(wthru_item);

    int unsigned count = 30;
    bit [31:0]   base  = 32'h0000_1000;
    bit [31:0]   span  = 32'h0000_0400;

    `uvm_object_utils(wthru_seq)

    function new(string name = "wthru_seq");
        super.new(name);
    endfunction

    task body();
        wthru_item item;
        repeat (count) begin
            item = wthru_item::type_id::create("wthru");
            start_item(item);
            if (!item.randomize() with { addr inside {[base : base + span - 4]}; })
                `uvm_fatal("SEQRAND", "wthru_item randomization failed")
            finish_item(item);
        end
    endtask

endclass

// Runs all three initiators at once, which is what makes the arbiter and the
// one-outstanding invariant interesting.
class axi_traffic_seq extends uvm_sequence;

    refill_sequencer i_sqr;
    refill_sequencer d_sqr;
    wthru_sequencer  w_sqr;

    int unsigned n_i_refill = 20;
    int unsigned n_d_refill = 20;
    int unsigned n_write    = 40;

    bit [31:0] read_base  = 32'h0000_0000;
    bit [31:0] read_span  = 32'h0000_0400;
    bit [31:0] write_base = 32'h0000_1000;
    bit [31:0] write_span = 32'h0000_0400;

    `uvm_object_utils(axi_traffic_seq)

    function new(string name = "axi_traffic_seq");
        super.new(name);
    endfunction

    task body();
        refill_seq i_seq;
        refill_seq d_seq;
        wthru_seq  w_seq;

        i_seq = refill_seq::type_id::create("i_seq");
        d_seq = refill_seq::type_id::create("d_seq");
        w_seq = wthru_seq::type_id::create("w_seq");

        i_seq.count = n_i_refill; i_seq.base = read_base;  i_seq.span = read_span;
        d_seq.count = n_d_refill; d_seq.base = read_base;  d_seq.span = read_span;
        w_seq.count = n_write;    w_seq.base = write_base; w_seq.span = write_span;

        fork
            i_seq.start(i_sqr);
            d_seq.start(d_sqr);
            w_seq.start(w_sqr);
        join
    endtask

endclass
