module {
  // func dialect: function definition
  func.func @compute_sum(%n: i32) -> i32 {
    // arith dialect: arithmetic operations
    %c0 = arith.constant 0 : i32
    %c1 = arith.constant 1 : i32
    %sum = arith.constant 0 : i32

    // scf dialect: structured control flow (for loop)
    %result = scf.for %i = %c0 to %n step %c1 iter_args(%acc = %sum) -> (i32) {
      %new_acc = arith.addi %acc, %i : i32
      scf.yield %new_acc : i32
    }

    func.return %result : i32
  }

  // scf.if: conditional execution
  func.func @conditional(%x: i32, %y: i32) -> i32 {
    %c0 = arith.constant 0 : i32
    %cmp = arith.cmpi "sgt", %x, %c0 : i32

    %result = scf.if %cmp -> (i32) {
      %sum = arith.addi %x, %y : i32
      scf.yield %sum : i32
    } else {
      %diff = arith.subi %x, %y : i32
      scf.yield %diff : i32
    }

    func.return %result : i32
  }
}
