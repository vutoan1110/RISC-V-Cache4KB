# DE2-115 onboard oscillator is 50 MHz: 20.000 ns period.
create_clock -name clk -period 20.000 [get_ports {clk}]

# These external controls are asynchronous to clk. The RTL reset is used as
# an asynchronous clear; UART synchronization is handled inside uart_core.
set_false_path -from [get_ports {reset_n}]
set_false_path -from [get_ports {key1_n}]
set_false_path -from [get_ports {uart_rx}]

# Board outputs. None of these sinks impose an FPGA-relevant setup/hold
# requirement at 50 MHz, so their register-to-pin paths are cut from timing
# analysis (this makes the STA sign-off complete instead of leaving them
# silently unconstrained):
#   - HEX0..7, LEDR    : human-visible 7-segment / LED indicators, no receiver.
#   - LCD_*            : HD44780 character LCD sequenced by lcd_1602_hex.v at a
#                        1 kHz tick; data/RS/RW/EN are stable for ~50,000 clocks
#                        around every enable edge.
#   - uart_tx          : 115200-baud line (~434 clocks/bit), oversampled by the
#                        external USB-UART bridge.
set_false_path -to [get_ports {HEX0[*] HEX1[*] HEX2[*] HEX3[*]}]
set_false_path -to [get_ports {HEX4[*] HEX5[*] HEX6[*] HEX7[*]}]
set_false_path -to [get_ports {LEDR[*]}]
set_false_path -to [get_ports {LCD_DATA[*]}]
set_false_path -to [get_ports {LCD_EN LCD_RS LCD_RW LCD_ON}]
set_false_path -to [get_ports {uart_tx}]

derive_clock_uncertainty
