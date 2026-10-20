module lcd_1602_hex #(
    parameter integer CLK_HZ = 50_000_000
)(
    input  wire        clk,
    input  wire        reset_n,
    input  wire [31:0] disp_value,

    output reg  [7:0]  LCD_DATA,
    output reg         LCD_EN,
    output reg         LCD_RS,
    output wire        LCD_RW,
    output wire        LCD_ON,
    output wire        LCD_BLON
);

    assign LCD_RW   = 1'b0;
    assign LCD_ON   = 1'b1;
    assign LCD_BLON = 1'b1;

    // 1ms tick
    localparam integer TICK_HZ = 1000;
    localparam integer DIV_MAX = (CLK_HZ / TICK_HZ) - 1;

    reg [$clog2(DIV_MAX+1)-1:0] div;
    reg tick;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            div  <= 0;
            tick <= 1'b0;
        end else begin
            if (div == DIV_MAX[$clog2(DIV_MAX+1)-1:0]) begin
                div  <= 0;
                tick <= 1'b1;
            end else begin
                div  <= div + 1'b1;
                tick <= 1'b0;
            end
        end
    end

    function automatic [7:0] hex_to_ascii(input [3:0] h);
        begin
            // h is a nibble; widen it explicitly for the 8-bit addition.
            if (h < 4'd10) hex_to_ascii = 8'd48 + {4'b0, h}; // '0'..'9'
            else           hex_to_ascii = 8'd55 + {4'b0, h}; // 'A'..'F'
        end
    endfunction

    // Build 16-char line buffer: 8 hex chars + 8 spaces
    wire [7:0] ch0 = hex_to_ascii(disp_value[31:28]);
    wire [7:0] ch1 = hex_to_ascii(disp_value[27:24]);
    wire [7:0] ch2 = hex_to_ascii(disp_value[23:20]);
    wire [7:0] ch3 = hex_to_ascii(disp_value[19:16]);
    wire [7:0] ch4 = hex_to_ascii(disp_value[15:12]);
    wire [7:0] ch5 = hex_to_ascii(disp_value[11: 8]);
    wire [7:0] ch6 = hex_to_ascii(disp_value[ 7: 4]);
    wire [7:0] ch7 = hex_to_ascii(disp_value[ 3: 0]);

    // Very conservative write FSM
    localparam [4:0]
        S_PWRUP_0   = 5'd0,
        S_PWRUP_1   = 5'd1,
        S_FUNC      = 5'd2,
        S_DISP_ON   = 5'd3,
        S_CLEAR     = 5'd4,
        S_ENTRY     = 5'd5,
        S_SET_DDRAM = 5'd6,
        S_WRITE_0   = 5'd7,
        S_WRITE_1   = 5'd8,
        S_WRITE_2   = 5'd9,
        S_WRITE_3   = 5'd10,
        S_WRITE_4   = 5'd11,
        S_WRITE_5   = 5'd12,
        S_WRITE_6   = 5'd13,
        S_WRITE_7   = 5'd14,
        S_WRITE_SP0 = 5'd15,
        S_WRITE_SP1 = 5'd16,
        S_WRITE_SP2 = 5'd17,
        S_WRITE_SP3 = 5'd18,
        S_WRITE_SP4 = 5'd19,
        S_WRITE_SP5 = 5'd20,
        S_WRITE_SP6 = 5'd21,
        S_WRITE_SP7 = 5'd22,
        S_HOLD      = 5'd23;

    reg [4:0] state;
    reg [1:0] en_phase; // 0: idle, 1: EN=1, 2: EN=0

    task automatic drive_byte(input rs, input [7:0] data);
        begin
            LCD_RS   <= rs;
            LCD_DATA <= data;
        end
    endtask

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state    <= S_PWRUP_0;
            en_phase <= 2'd0;
            LCD_EN   <= 1'b0;
            LCD_RS   <= 1'b0;
            LCD_DATA <= 8'h00;
        end else if (tick) begin
            // simple 1ms-tick 3-phase EN pulse
            case (en_phase)
                2'd0: begin
                    // load next byte for current state, then raise EN
                    case (state)
                        S_PWRUP_0:   drive_byte(1'b0, 8'h38);
                        S_PWRUP_1:   drive_byte(1'b0, 8'h38);
                        S_FUNC:      drive_byte(1'b0, 8'h38); // 8-bit, 2 lines
                        S_DISP_ON:   drive_byte(1'b0, 8'h0C); // display on, cursor off
                        S_CLEAR:     drive_byte(1'b0, 8'h01); // clear
                        S_ENTRY:     drive_byte(1'b0, 8'h06); // entry mode
                        S_SET_DDRAM: drive_byte(1'b0, 8'h80); // line1 addr 0
                        S_WRITE_0:   drive_byte(1'b1, ch0);
                        S_WRITE_1:   drive_byte(1'b1, ch1);
                        S_WRITE_2:   drive_byte(1'b1, ch2);
                        S_WRITE_3:   drive_byte(1'b1, ch3);
                        S_WRITE_4:   drive_byte(1'b1, ch4);
                        S_WRITE_5:   drive_byte(1'b1, ch5);
                        S_WRITE_6:   drive_byte(1'b1, ch6);
                        S_WRITE_7:   drive_byte(1'b1, ch7);
                        default:     drive_byte(1'b1, 8'h20); // spaces
                    endcase
                    LCD_EN   <= 1'b1;
                    en_phase <= 2'd1;
                end
                2'd1: begin
                    // drop EN
                    LCD_EN   <= 1'b0;
                    en_phase <= 2'd2;
                end
                default: begin
                    // advance state
                    en_phase <= 2'd0;
                    case (state)
                        S_PWRUP_0:   state <= S_PWRUP_1;
                        S_PWRUP_1:   state <= S_FUNC;
                        S_FUNC:      state <= S_DISP_ON;
                        S_DISP_ON:   state <= S_CLEAR;
                        S_CLEAR:     state <= S_ENTRY;
                        S_ENTRY:     state <= S_SET_DDRAM;
                        S_SET_DDRAM: state <= S_WRITE_0;
                        S_WRITE_0:   state <= S_WRITE_1;
                        S_WRITE_1:   state <= S_WRITE_2;
                        S_WRITE_2:   state <= S_WRITE_3;
                        S_WRITE_3:   state <= S_WRITE_4;
                        S_WRITE_4:   state <= S_WRITE_5;
                        S_WRITE_5:   state <= S_WRITE_6;
                        S_WRITE_6:   state <= S_WRITE_7;
                        S_WRITE_7:   state <= S_WRITE_SP0;
                        S_WRITE_SP0: state <= S_WRITE_SP1;
                        S_WRITE_SP1: state <= S_WRITE_SP2;
                        S_WRITE_SP2: state <= S_WRITE_SP3;
                        S_WRITE_SP3: state <= S_WRITE_SP4;
                        S_WRITE_SP4: state <= S_WRITE_SP5;
                        S_WRITE_SP5: state <= S_WRITE_SP6;
                        S_WRITE_SP6: state <= S_WRITE_SP7;
                        S_WRITE_SP7: state <= S_HOLD;
                        S_HOLD:      state <= S_SET_DDRAM; // rewrite periodically
                        default:     state <= S_SET_DDRAM;
                    endcase
                end
            endcase
        end
    end

endmodule
