// Exercises what the directed program never touches: the APB peripherals, the
// register model, the UART serial line and an end-to-end timer interrupt.
//
// The program is verification/uvm/seq/soc_periph_irq.hex, built by
// gen_soc_periph_irq.py in the same directory. It configures the UART and
// sends a byte, reads the sysmon identification register, arms the timer,
// spins until the handler sets x31, and halts.
class soc_periph_test extends soc_base_test;

    `uvm_component_utils(soc_periph_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void configure();
        cfg.expected_retire = 0;        // the program length is not a golden number
        cfg.timeout_cycles  = 200000;
        // hdl/baudrate_gen_block.sv: 16 oversample ticks of 28 clocks per bit.
        cfg.uart_bit_cycles = 448;
    endfunction

    function void check_phase(uvm_phase phase);
        super.check_phase(phase);

        if (cfg.stats.apb_write == 0)
            `uvm_error("NOAPBWRITE", "the program made no APB write")
        if (cfg.stats.apb_read == 0)
            `uvm_error("NOAPBREAD", "the program made no APB read")

        // The handler runs only if the timer interrupt was delivered, and the
        // flag it sets ends the spin loop.
        if (cfg.stats.irq_taken == 0)
            `uvm_error("NOIRQ", "no interrupt redirect was observed")
        if (cfg.stats.uart_tx_bytes == 0)
            `uvm_error("NOUART", "no byte came out on uart_tx")

        if (cfg.stats.arch_regs[31] !== 32'd1)
            `uvm_error("NOIRQ",
                $sformatf("x31 is %0d, so the timer interrupt handler never completed",
                          cfg.stats.arch_regs[31]))

        check_reg("uart.cfg",    cfg.regs.uart.cfg,    32'h0000_00c3);
        check_reg("timer.cmp",   cfg.regs.timer.cmp,   32'd20);
        check_reg("sysmon.ident", cfg.regs.sysmon.ident, 32'h5338_0002);
    endfunction

    // The mirrored value comes from the APB monitor, so this compares what the
    // register model predicted against what the design was told or reported.
    protected function void check_reg(string name, uvm_reg r,
                                      uvm_reg_data_t expected);
        uvm_reg_data_t got = r.get_mirrored_value();
        if (got !== expected)
            `uvm_error("REGMIRROR",
                $sformatf("%s mirrored 0x%08h, expected 0x%08h", name, got, expected))
        else
            `uvm_info("REGMIRROR",
                $sformatf("%s mirrored 0x%08h as expected", name, got), UVM_LOW)
    endfunction

endclass
