// UART serial agent. The monitor decodes 8N1 frames the DUT transmits on
// uart_tx; the driver sends 8N1 frames into uart_rx.
//
// The bit period comes from soc_cfg::uart_bit_cycles and has to match the
// divider the firmware programs into hdl/uart_apb.v.

class uart_sequencer extends uvm_sequencer #(uart_byte_item);
    `uvm_component_utils(uart_sequencer)
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass

class uart_driver extends uvm_driver #(uart_byte_item);

    virtual uart_if vif;
    soc_cfg         cfg;

    `uvm_component_utils(uart_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for uart_driver")
    endfunction

    protected task bit_time();
        repeat (cfg.uart_bit_cycles) @(posedge vif.clk);
    endtask

    task run_phase(uvm_phase phase);
        uart_byte_item item;

        vif.uart_rx = 1'b1;             // idle high
        wait (vif.reset_n === 1'b1);

        forever begin
            seq_item_port.get_next_item(item);

            vif.uart_rx = 1'b0;         // start bit
            bit_time();
            for (int b = 0; b < 8; b++) begin
                vif.uart_rx = item.data[b];
                bit_time();
            end
            vif.uart_rx = 1'b1;         // stop bit
            bit_time();

            cfg.stats.uart_rx_bytes++;
            `uvm_info("UARTTX", $sformatf("sent 0x%02h into uart_rx", item.data), UVM_MEDIUM)
            seq_item_port.item_done();
        end
    endtask

endclass

class uart_monitor extends uvm_monitor;

    virtual uart_if vif;
    soc_cfg         cfg;

    uvm_analysis_port #(uart_byte_item) ap;

    `uvm_component_utils(uart_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for uart_monitor")
    endfunction

    protected task bit_time();
        repeat (cfg.uart_bit_cycles) @(posedge vif.clk);
    endtask

    protected task half_bit_time();
        repeat (cfg.uart_bit_cycles / 2) @(posedge vif.clk);
    endtask

    task run_phase(uvm_phase phase);
        uart_byte_item   item;
        bit [7:0]        data;
        longint unsigned cyc;

        cyc = 0;
        wait (vif.reset_n === 1'b1);
        // The line has to be idle high before a falling edge means anything;
        // otherwise the X-to-1 settling at reset looks like a start bit.
        wait (vif.uart_tx === 1'b1);

        forever begin
            // Wait for a start bit.
            @(negedge vif.uart_tx);

            // Sample in the middle of each bit.
            half_bit_time();
            if (vif.uart_tx !== 1'b0)
                continue;               // glitch, not a real start bit

            for (int b = 0; b < 8; b++) begin
                bit_time();
                data[b] = vif.uart_tx;
            end

            bit_time();
            item               = uart_byte_item::type_id::create("uart_byte");
            item.data          = data;
            item.framing_error = (vif.uart_tx !== 1'b1);
            item.cycle         = cyc;

            if (item.framing_error)
                `uvm_error("UARTFRAME",
                    $sformatf("stop bit missing after byte 0x%02h", data))

            cfg.stats.uart_tx_bytes++;
            `uvm_info("UARTRX", $sformatf("observed 0x%02h on uart_tx", data), UVM_MEDIUM)
            ap.write(item);
        end
    endtask

endclass

class uart_agent extends uvm_agent;

    uart_driver    driver;
    uart_monitor   monitor;
    uart_sequencer sequencer;

    soc_cfg cfg;

    `uvm_component_utils(uart_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for uart_agent")

        monitor     = uart_monitor::type_id::create("monitor", this);
        monitor.vif = cfg.uart_vif;

        sequencer   = uart_sequencer::type_id::create("sequencer", this);
        driver      = uart_driver::type_id::create("driver", this);
        driver.vif  = cfg.uart_vif;
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
