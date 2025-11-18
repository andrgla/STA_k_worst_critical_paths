module top (
    \opcode[0] ,
    \opcode[1] ,
    \opcode[2] ,
    \sel_reg_dst[0] ,
    \sel_reg_dst[1] ,
    \alu_op[0]
);

  // Inputs
  input  \opcode[0] ,
         \opcode[1] ,
         \opcode[2] ;

  // Outputs
  output \sel_reg_dst[0] ,
         \sel_reg_dst[1] ,
         \alu_op[0] ;

  // Internal nets
  wire n0, n1, n2, n3, n4, n5;

  // Simple logic to generate a small DAG:
  // n0 = opcode[0] & ~opcode[1]
  assign n0 = \opcode[0]  & ~\opcode[1] ;

  // n1 = opcode[2] & opcode[1]
  assign n1 = \opcode[2]  &  \opcode[1] ;

  // n2 = ~opcode[2]
  assign n2 = ~\opcode[2] ;

  // n3 = n0 | n1
  assign n3 = n0 | n1;

  // n4 = n2 & opcode[0]
  assign n4 = n2 & \opcode[0] ;

  // n5 = n3 & ~n4
  assign n5 = n3 & ~n4;

  // Outputs
  assign \sel_reg_dst[0]  = n3;
  assign \sel_reg_dst[1]  = n4;
  assign \alu_op[0]       = n5;

endmodule
