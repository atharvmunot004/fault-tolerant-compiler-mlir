module {
  // Control flow example with blocks
  func.func @conditional(%arg0: i32) -> i32 {
    // Constants
    %c10 = arith.constant 10 : i32
    %c1 = arith.constant 1 : i32
    %c2 = arith.constant 2 : i32

    // Compare operation
    %cond = arith.cmpi "slt", %arg0, %c10 : i32

    // Conditional branch: terminator that takes control flow
    cf.cond_br %cond, ^bb1, ^bb2

  ^bb1:  // Block label
    // Block argument: %arg0 flows here
    %result = arith.addi %arg0, %c1 : i32
    cf.br ^bb3(%result : i32)  // Branch with argument

  ^bb2:
    %result2 = arith.muli %arg0, %c2 : i32
    cf.br ^bb3(%result2 : i32)

  ^bb3(%val: i32):  // Block with argument
    func.return %val : i32
  }
}
