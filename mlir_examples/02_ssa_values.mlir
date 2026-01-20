module {
  // Function definition: @name is a symbol, %arg0 is a block argument
  func.func @add_numbers(%arg0: i32, %arg1: i32) -> i32 {
    // %0 is an SSA value (result of arith.addi operation)
    %0 = arith.addi %arg0, %arg1 : i32

    // %1 is another SSA value
    %1 = arith.muli %0, %0 : i32

    // Terminator: ends the block
    func.return %1 : i32
  }
}
