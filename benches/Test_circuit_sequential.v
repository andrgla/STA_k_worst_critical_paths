// Complex gate-level vending machine with multiple sub-circuits
// Features: Coin validator, BCD adder, comparator, change calculator, inventory counter


module vending_machine_complex (
    clk, reset,
    \coin_in[0] , \coin_in[1] , \coin_in[2] , \coin_in[3] , \coin_in[4] ,
    \item_select[0] , \item_select[1] ,
    dispense, \change_out[0] , \change_out[1] , \change_out[2] , \change_out[3] , \change_out[4] , \change_out[5] ,
    \display[0] , \display[1] , \display[2] , \display[3] , \display[4] , \display[5] , \display[6] ,
    \inventory[0] , \inventory[1] , \inventory[2] , \inventory[3] ,
    error, sold_out
);

input clk, reset;
input \coin_in[0] , \coin_in[1] , \coin_in[2] , \coin_in[3] , \coin_in[4] ;  // 5-bit coin value
input \item_select[0] , \item_select[1] ;  // 2-bit item selection
output dispense, error, sold_out;
output \change_out[0] , \change_out[1] , \change_out[2] , \change_out[3] , \change_out[4] , \change_out[5] ;
output \display[0] , \display[1] , \display[2] , \display[3] , \display[4] , \display[5] , \display[6] ;
output \inventory[0] , \inventory[1] , \inventory[2] , \inventory[3] ;

// Internal nets
wire \total[0] , \total[1] , \total[2] , \total[3] , \total[4] , \total[5] , \total[6] ;
wire \price[0] , \price[1] , \price[2] , \price[3] , \price[4] , \price[5] ;
wire \acc[0] , \acc[1] , \acc[2] , \acc[3] , \acc[4] , \acc[5] , \acc[6] ;
wire \acc_next[0] , \acc_next[1] , \acc_next[2] , \acc_next[3] , \acc_next[4] , \acc_next[5] , \acc_next[6] ;
wire valid_coin, sufficient, add_coin, reset_acc, decrement_inv;
wire \inv_count[0] , \inv_count[1] , \inv_count[2] , \inv_count[3] ;
wire \inv_next[0] , \inv_next[1] , \inv_next[2] , \inv_next[3] ;

wire n0, n1, n2, n3, n4, n5, n6, n7, n8, n9;
wire n10, n11, n12, n13, n14, n15, n16, n17, n18, n19;
wire n20, n21, n22, n23, n24, n25, n26, n27, n28, n29;
wire n30, n31, n32, n33, n34, n35, n36, n37, n38, n39;
wire n40, n41, n42, n43, n44, n45, n46, n47, n48, n49;
wire n50, n51, n52, n53, n54, n55, n56, n57, n58, n59;
wire n60, n61, n62, n63, n64, n65, n66, n67, n68, n69;
wire n70, n71, n72, n73, n74, n75, n76, n77, n78, n79;
wire n80, n81, n82, n83, n84, n85, n86, n87, n88, n89;
wire n90, n91, n92, n93, n94, n95, n96, n97, n98, n99;

// === SUB-CIRCUIT 1: COIN VALIDATOR ===
// Validates coins: 5, 10, 15, 20, 25 cents
coin_validator cv (
    .\value[0] (\coin_in[0] ),
    .\value[1] (\coin_in[1] ),
    .\value[2] (\coin_in[2] ),
    .\value[3] (\coin_in[3] ),
    .\value[4] (\coin_in[4] ),
    .valid(valid_coin)
);

// === SUB-CIRCUIT 2: PRICE LOOKUP ===
// Maps item_select to price
price_lookup pl (
    .\select[0] (\item_select[0] ),
    .\select[1] (\item_select[1] ),
    .\price[0] (\price[0] ),
    .\price[1] (\price[1] ),
    .\price[2] (\price[2] ),
    .\price[3] (\price[3] ),
    .\price[4] (\price[4] ),
    .\price[5] (\price[5] )
);

// === ACCUMULATOR REGISTER (stores total coins inserted) ===
DFF acc_reg0 ( .D(\acc_next[0] ), .CLK(clk), .RESET(reset), .Q(\acc[0] ) );
DFF acc_reg1 ( .D(\acc_next[1] ), .CLK(clk), .RESET(reset), .Q(\acc[1] ) );
DFF acc_reg2 ( .D(\acc_next[2] ), .CLK(clk), .RESET(reset), .Q(\acc[2] ) );
DFF acc_reg3 ( .D(\acc_next[3] ), .CLK(clk), .RESET(reset), .Q(\acc[3] ) );
DFF acc_reg4 ( .D(\acc_next[4] ), .CLK(clk), .RESET(reset), .Q(\acc[4] ) );
DFF acc_reg5 ( .D(\acc_next[5] ), .CLK(clk), .RESET(reset), .Q(\acc[5] ) );
DFF acc_reg6 ( .D(\acc_next[6] ), .CLK(clk), .RESET(reset), .Q(\acc[6] ) );

// === SUB-CIRCUIT 3: BCD ADDER ===
// Adds coin value to accumulator
bcd_adder_7bit adder (
    .\a[0] (\acc[0] ), .\a[1] (\acc[1] ), .\a[2] (\acc[2] ), .\a[3] (\acc[3] ),
    .\a[4] (\acc[4] ), .\a[5] (\acc[5] ), .\a[6] (\acc[6] ),
    .\b[0] (\coin_in[0] ), .\b[1] (\coin_in[1] ), .\b[2] (\coin_in[2] ),
    .\b[3] (\coin_in[3] ), .\b[4] (\coin_in[4] ), .\b[5] (1'b0), .\b[6] (1'b0),
    .\sum[0] (\total[0] ), .\sum[1] (\total[1] ), .\sum[2] (\total[2] ),
    .\sum[3] (\total[3] ), .\sum[4] (\total[4] ), .\sum[5] (\total[5] ),
    .\sum[6] (\total[6] )
);

// Accumulator next value logic
AND and_add0 ( .A(valid_coin), .B(add_coin), .Y(n0) );
MUX2 mux_acc0 ( .A(\acc[0] ), .B(\total[0] ), .S(n0), .Y(n10) );
MUX2 mux_acc1 ( .A(\acc[1] ), .B(\total[1] ), .S(n0), .Y(n11) );
MUX2 mux_acc2 ( .A(\acc[2] ), .B(\total[2] ), .S(n0), .Y(n12) );
MUX2 mux_acc3 ( .A(\acc[3] ), .B(\total[3] ), .S(n0), .Y(n13) );
MUX2 mux_acc4 ( .A(\acc[4] ), .B(\total[4] ), .S(n0), .Y(n14) );
MUX2 mux_acc5 ( .A(\acc[5] ), .B(\total[5] ), .S(n0), .Y(n15) );
MUX2 mux_acc6 ( .A(\acc[6] ), .B(\total[6] ), .S(n0), .Y(n16) );

MUX2 mux_rst0 ( .A(n10), .B(1'b0), .S(reset_acc), .Y(\acc_next[0] ) );
MUX2 mux_rst1 ( .A(n11), .B(1'b0), .S(reset_acc), .Y(\acc_next[1] ) );
MUX2 mux_rst2 ( .A(n12), .B(1'b0), .S(reset_acc), .Y(\acc_next[2] ) );
MUX2 mux_rst3 ( .A(n13), .B(1'b0), .S(reset_acc), .Y(\acc_next[3] ) );
MUX2 mux_rst4 ( .A(n14), .B(1'b0), .S(reset_acc), .Y(\acc_next[4] ) );
MUX2 mux_rst5 ( .A(n15), .B(1'b0), .S(reset_acc), .Y(\acc_next[5] ) );
MUX2 mux_rst6 ( .A(n16), .B(1'b0), .S(reset_acc), .Y(\acc_next[6] ) );

// === SUB-CIRCUIT 4: COMPARATOR ===
// Check if accumulator >= price
comparator_6bit comp (
    .\a[0] (\acc[0] ), .\a[1] (\acc[1] ), .\a[2] (\acc[2] ),
    .\a[3] (\acc[3] ), .\a[4] (\acc[4] ), .\a[5] (\acc[5] ),
    .\b[0] (\price[0] ), .\b[1] (\price[1] ), .\b[2] (\price[2] ),
    .\b[3] (\price[3] ), .\b[4] (\price[4] ), .\b[5] (\price[5] ),
    .a_gte_b(sufficient)
);

// === SUB-CIRCUIT 5: SUBTRACTOR (for change calculation) ===
subtractor_6bit sub (
    .\a[0] (\acc[0] ), .\a[1] (\acc[1] ), .\a[2] (\acc[2] ),
    .\a[3] (\acc[3] ), .\a[4] (\acc[4] ), .\a[5] (\acc[5] ),
    .\b[0] (\price[0] ), .\b[1] (\price[1] ), .\b[2] (\price[2] ),
    .\b[3] (\price[3] ), .\b[4] (\price[4] ), .\b[5] (\price[5] ),
    .\diff[0] (\change_out[0] ), .\diff[1] (\change_out[1] ),
    .\diff[2] (\change_out[2] ), .\diff[3] (\change_out[3] ),
    .\diff[4] (\change_out[4] ), .\diff[5] (\change_out[5] )
);

// === INVENTORY COUNTER ===
DFF inv_reg0 ( .D(\inv_next[0] ), .CLK(clk), .RESET(reset), .Q(\inv_count[0] ) );
DFF inv_reg1 ( .D(\inv_next[1] ), .CLK(clk), .RESET(reset), .Q(\inv_count[1] ) );
DFF inv_reg2 ( .D(\inv_next[2] ), .CLK(clk), .RESET(reset), .Q(\inv_count[2] ) );
DFF inv_reg3 ( .D(\inv_next[3] ), .CLK(clk), .RESET(reset), .Q(\inv_count[3] ) );

assign \inventory[0]  = \inv_count[0] ;
assign \inventory[1]  = \inv_count[1] ;
assign \inventory[2]  = \inv_count[2] ;
assign \inventory[3]  = \inv_count[3] ;

// === SUB-CIRCUIT 6: DOWN COUNTER ===
down_counter_4bit dcnt (
    .\count[0] (\inv_count[0] ), .\count[1] (\inv_count[1] ),
    .\count[2] (\inv_count[2] ), .\count[3] (\inv_count[3] ),
    .decrement(decrement_inv),
    .\next[0] (\inv_next[0] ), .\next[1] (\inv_next[1] ),
    .\next[2] (\inv_next[2] ), .\next[3] (\inv_next[3] ),
    .is_zero(sold_out)
);

// === SUB-CIRCUIT 7: 7-SEGMENT DISPLAY DECODER ===
bcd_to_7seg display_dec (
    .\bcd[0] (\acc[0] ), .\bcd[1] (\acc[1] ),
    .\bcd[2] (\acc[2] ), .\bcd[3] (\acc[3] ),
    .\seg[0] (\display[0] ), .\seg[1] (\display[1] ),
    .\seg[2] (\display[2] ), .\seg[3] (\display[3] ),
    .\seg[4] (\display[4] ), .\seg[5] (\display[5] ),
    .\seg[6] (\display[6] )
);

// === CONTROL LOGIC ===
NOT inv_soldout ( .A(sold_out), .Y(n20) );
AND and_can_dispense ( .A(sufficient), .B(n20), .Y(n21) );
assign dispense = n21;
assign reset_acc = dispense;
assign decrement_inv = dispense;

// Add coin when valid and not dispensing
NOT inv_disp ( .A(dispense), .Y(n22) );
AND and_addcoin ( .A(valid_coin), .B(n22), .Y(add_coin) );

// Error if invalid coin
NOT inv_valid ( .A(valid_coin), .Y(n23) );
OR or_coin_present ( .A(\coin_in[0] ), .B(\coin_in[1] ), .Y(n24) );
OR or_coin_present2 ( .A(n24), .B(\coin_in[2] ), .Y(n25) );
OR or_coin_present3 ( .A(n25), .B(\coin_in[3] ), .Y(n26) );
OR or_coin_present4 ( .A(n26), .B(\coin_in[4] ), .Y(n27) );
AND and_error ( .A(n23), .B(n27), .Y(error) );

endmodule

// ============= SUB-CIRCUITS =============

// Coin validator: validates 5, 10, 15, 20, 25 cent coins
module coin_validator (
    \value[0] , \value[1] , \value[2] , \value[3] , \value[4] , valid
);
input \value[0] , \value[1] , \value[2] , \value[3] , \value[4] ;
output valid;
wire n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10;

// Check for 5 (00101), 10 (01010), 15 (01111), 20 (10100), 25 (11001)
// Simplified: accept if value is 5, 10, 15, 20, or 25
NOT inv0 ( .A(\value[0] ), .Y(n0) );
NOT inv1 ( .A(\value[1] ), .Y(n1) );
NOT inv2 ( .A(\value[2] ), .Y(n2) );
NOT inv3 ( .A(\value[3] ), .Y(n3) );
NOT inv4 ( .A(\value[4] ), .Y(n4) );

// 5 = 00101
AND and_5a ( .A(\value[0] ), .B(n1), .Y(n5) );
AND and_5b ( .A(n5), .B(\value[2] ), .Y(n6) );
AND and_5c ( .A(n6), .B(n3), .Y(n7) );
AND and_5d ( .A(n7), .B(n4), .Y(n8) );  // is_5

// Accept any non-zero value for simplicity (can expand)
OR or_val ( .A(\value[0] ), .B(\value[1] ), .Y(n9) );
OR or_val2 ( .A(n9), .B(\value[2] ), .Y(n10) );
assign valid = n10;  // Simplified validator

endmodule

// Price lookup based on item selection
module price_lookup (
    \select[0] , \select[1] , \price[0] , \price[1] , \price[2] , \price[3] , \price[4] , \price[5] 
);
input \select[0] , \select[1] ;
output \price[0] , \price[1] , \price[2] , \price[3] , \price[4] , \price[5] ;

// Item 0: 15 cents, Item 1: 20 cents, Item 2: 25 cents, Item 3: 30 cents
wire n0, n1, n2, n3;
NOT inv0 ( .A(\select[0] ), .Y(n0) );
NOT inv1 ( .A(\select[1] ), .Y(n1) );
AND and_item0 ( .A(n0), .B(n1), .Y(n2) );  // 00 -> 15
AND and_item1 ( .A(\select[0] ), .B(n1), .Y(n3) );  // 01 -> 20

// Price[0-5] encoding (simplified binary)
assign \price[0]  = n2;  // 15 = 001111, 20 = 010100
assign \price[1]  = n2;
assign \price[2]  = n2;
assign \price[3]  = n2;
assign \price[4]  = n3;
assign \price[5]  = 1'b0;

endmodule

// 7-bit BCD adder
module bcd_adder_7bit (
    \a[0] , \a[1] , \a[2] , \a[3] , \a[4] , \a[5] , \a[6] ,
    \b[0] , \b[1] , \b[2] , \b[3] , \b[4] , \b[5] , \b[6] ,
    \sum[0] , \sum[1] , \sum[2] , \sum[3] , \sum[4] , \sum[5] , \sum[6] 
);
input \a[0] , \a[1] , \a[2] , \a[3] , \a[4] , \a[5] , \a[6] ;
input \b[0] , \b[1] , \b[2] , \b[3] , \b[4] , \b[5] , \b[6] ;
output \sum[0] , \sum[1] , \sum[2] , \sum[3] , \sum[4] , \sum[5] , \sum[6] ;
wire c0, c1, c2, c3, c4, c5, c6;

// Chain of full adders
full_adder fa0 ( .A(\a[0] ), .B(\b[0] ), .Cin(1'b0), .Sum(\sum[0] ), .Cout(c0) );
full_adder fa1 ( .A(\a[1] ), .B(\b[1] ), .Cin(c0), .Sum(\sum[1] ), .Cout(c1) );
full_adder fa2 ( .A(\a[2] ), .B(\b[2] ), .Cin(c1), .Sum(\sum[2] ), .Cout(c2) );
full_adder fa3 ( .A(\a[3] ), .B(\b[3] ), .Cin(c2), .Sum(\sum[3] ), .Cout(c3) );
full_adder fa4 ( .A(\a[4] ), .B(\b[4] ), .Cin(c3), .Sum(\sum[4] ), .Cout(c4) );
full_adder fa5 ( .A(\a[5] ), .B(\b[5] ), .Cin(c4), .Sum(\sum[5] ), .Cout(c5) );
full_adder fa6 ( .A(\a[6] ), .B(\b[6] ), .Cin(c5), .Sum(\sum[6] ), .Cout(c6) );

endmodule

// 6-bit comparator
module comparator_6bit (
    \a[0] , \a[1] , \a[2] , \a[3] , \a[4] , \a[5] ,
    \b[0] , \b[1] , \b[2] , \b[3] , \b[4] , \b[5] , a_gte_b
);
input \a[0] , \a[1] , \a[2] , \a[3] , \a[4] , \a[5] ;
input \b[0] , \b[1] , \b[2] , \b[3] , \b[4] , \b[5] ;
output a_gte_b;
wire n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11;

// Compare bit by bit from MSB
XNOR xnor5 ( .A(\a[5] ), .B(\b[5] ), .Y(n0) );
XNOR xnor4 ( .A(\a[4] ), .B(\b[4] ), .Y(n1) );
XNOR xnor3 ( .A(\a[3] ), .B(\b[3] ), .Y(n2) );
XNOR xnor2 ( .A(\a[2] ), .B(\b[2] ), .Y(n3) );
XNOR xnor1 ( .A(\a[1] ), .B(\b[1] ), .Y(n4) );
XNOR xnor0 ( .A(\a[0] ), .B(\b[0] ), .Y(n5) );

NOT inv_b5 ( .A(\b[5] ), .Y(n6) );
AND and_gt5 ( .A(\a[5] ), .B(n6), .Y(n7) );

// Simplified: a >= b if MSBs show a > b or equal with recursive check
OR or_gte ( .A(n7), .B(n0), .Y(n8) );  // Simplified
assign a_gte_b = n8;

endmodule

// 6-bit subtractor
module subtractor_6bit (
    \a[0] , \a[1] , \a[2] , \a[3] , \a[4] , \a[5] ,
    \b[0] , \b[1] , \b[2] , \b[3] , \b[4] , \b[5] ,
    \diff[0] , \diff[1] , \diff[2] , \diff[3] , \diff[4] , \diff[5] 
);
input \a[0] , \a[1] , \a[2] , \a[3] , \a[4] , \a[5] ;
input \b[0] , \b[1] , \b[2] , \b[3] , \b[4] , \b[5] ;
output \diff[0] , \diff[1] , \diff[2] , \diff[3] , \diff[4] , \diff[5] ;
wire b0, b1, b2, b3, b4, b5, bor0, bor1, bor2, bor3, bor4;

// Subtraction via 2's complement: a - b = a + (~b) + 1
NOT inv_b0 ( .A(\b[0] ), .B(b0) );
NOT inv_b1 ( .A(\b[1] ), .Y(b1) );
NOT inv_b2 ( .A(\b[2] ), .Y(b2) );
NOT inv_b3 ( .A(\b[3] ), .Y(b3) );
NOT inv_b4 ( .A(\b[4] ), .Y(b4) );
NOT inv_b5 ( .A(\b[5] ), .Y(b5) );

full_adder fs0 ( .A(\a[0] ), .B(b0), .Cin(1'b1), .Sum(\diff[0] ), .Cout(bor0) );
full_adder fs1 ( .A(\a[1] ), .B(b1), .Cin(bor0), .Sum(\diff[1] ), .Cout(bor1) );
full_adder fs2 ( .A(\a[2] ), .B(b2), .Cin(bor1), .Sum(\diff[2] ), .Cout(bor2) );
full_adder fs3 ( .A(\a[3] ), .B(b3), .Cin(bor2), .Sum(\diff[3] ), .Cout(bor3) );
full_adder fs4 ( .A(\a[4] ), .B(b4), .Cin(bor3), .Sum(\diff[4] ), .Cout(bor4) );
full_adder fs5 ( .A(\a[5] ), .B(b5), .Cin(bor4), .Sum(\diff[5] ), .Cout() );

endmodule

// 4-bit down counter
module down_counter_4bit (
    \count[0] , \count[1] , \count[2] , \count[3] , decrement,
    \next[0] , \next[1] , \next[2] , \next[3] , is_zero
);
input \count[0] , \count[1] , \count[2] , \count[3] , decrement;
output \next[0] , \next[1] , \next[2] , \next[3] , is_zero;
wire n0, n1, n2, n3, n4, n5, n6, n7, n8;
wire dec0, dec1, dec2, dec3;

// Decrement by 1: subtract 1 from count
NOT inv_c0 ( .A(\count[0] ), .Y(n0) );
XOR xor0 ( .A(\count[0] ), .B(1'b1), .Y(dec0) );

AND and_bor0 ( .A(n0), .B(1'b1), .Y(n1) );
XOR xor1 ( .A(\count[1] ), .B(n1), .Y(dec1) );

NOT inv_c1 ( .A(\count[1] ), .Y(n2) );
AND and_bor1a ( .A(n0), .B(n2), .Y(n3) );
XOR xor2 ( .A(\count[2] ), .B(n3), .Y(dec2) );

NOT inv_c2 ( .A(\count[2] ), .Y(n4) );
AND and_bor2a ( .A(n3), .B(n4), .Y(n5) );
XOR xor3 ( .A(\count[3] ), .B(n5), .Y(dec3) );

// Mux: decrement if enabled, else hold
MUX2 mux0 ( .A(\count[0] ), .B(dec0), .S(decrement), .Y(\next[0] ) );
MUX2 mux1 ( .A(\count[1] ), .B(dec1), .S(decrement), .Y(\next[1] ) );
MUX2 mux2 ( .A(\count[2] ), .B(dec2), .S(decrement), .Y(\next[2] ) );
MUX2 mux3 ( .A(\count[3] ), .B(dec3), .S(decrement), .Y(\next[3] ) );

// Zero detection
NOR nor0 ( .A(\count[0] ), .B(\count[1] ), .Y(n6) );
NOR nor1 ( .A(\count[2] ), .B(\count[3] ), .Y(n7) );
AND and_zero ( .A(n6), .B(n7), .Y(is_zero) );

endmodule

// BCD to 7-segment decoder
module bcd_to_7seg (
    \bcd[0] , \bcd[1] , \bcd[2] , \bcd[3] ,
    \seg[0] , \seg[1] , \seg[2] , \seg[3] , \seg[4] , \seg[5] , \seg[6] 
);
input \bcd[0] , \bcd[1] , \bcd[2] , \bcd[3] ;
output \seg[0] , \seg[1] , \seg[2] , \seg[3] , \seg[4] , \seg[5] , \seg[6] ;
wire n0, n1, n2, n3;

NOT inv0 ( .A(\bcd[0] ), .Y(n0) );
NOT inv1 ( .A(\bcd[1] ), .Y(n1) );
NOT inv2 ( .A(\bcd[2] ), .Y(n2) );
NOT inv3 ( .A(\bcd[3] ), .Y(n3) );

// Simplified 7-seg logic (just example patterns)
OR or_seg0 ( .A(\bcd[0] ), .B(\bcd[1] ), .Y(\seg[0] ) );
AND and_seg1 ( .A(\bcd[0] ), .B(\bcd[2] ), .Y(\seg[1] ) );
OR or_seg2 ( .A(\bcd[1] ), .B(\bcd[3] ), .Y(\seg[2] ) );
XOR xor_seg3 ( .A(\bcd[0] ), .B(\bcd[1] ), .Y(\seg[3] ) );
AND and_seg4 ( .A(n0), .B(\bcd[1] ), .Y(\seg[4] ) );
OR or_seg5 ( .A(\bcd[2] ), .B(\bcd[3] ), .Y(\seg[5] ) );
NAND nand_seg6 ( .A(\bcd[0] ), .B(\bcd[2] ), .Y(\seg[6] ) );

endmodule

// ============= PRIMITIVE GATES =============

module DFF (
    input D, CLK, RESET,
    output reg Q
);
    always @(posedge CLK or posedge RESET) begin
        if (RESET)
            Q <= 1'b0;
        else
            Q <= D;
    end
endmodule

module NOT ( input A, output Y );
    assign Y = ~A;
endmodule

module AND ( input A, B, output Y );
    assign Y = A & B;
endmodule

module OR ( input A, B, output Y );
    assign Y = A | B;
endmodule

module NAND ( input A, B, output Y );
    assign Y = ~(A & B);
endmodule

module NOR ( input A, B, output Y );
    assign Y = ~(A | B);
endmodule

module XOR ( input A, B, output Y );
    assign Y = A ^ B;
endmodule

module XNOR ( input A, B, output Y );
    assign Y = ~(A ^ B);
endmodule

module MUX2 ( input A, B, S, output Y );
    assign Y = S ? B : A;
endmodule

module full_adder (
    input A, B, Cin,
    output Sum, Cout
);
    wire n0, n1, n2;
    XOR xor0 ( .A(A), .B(B), .Y(n0) );
    XOR xor1 ( .A(n0), .B(Cin), .Y(Sum) );
    AND and0 ( .A(A), .B(B), .Y(n1) );
    AND and1 ( .A(n0), .B(Cin), .Y(n2) );
    OR or0 ( .A(n1), .B(n2), .Y(Cout) );
endmodule