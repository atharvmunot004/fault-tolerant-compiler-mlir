module {
  // cf dialect: unstructured control flow
  func.func @branch_example(%x: i32) -> i32 {
    %c10 = arith.constant 10 : i32
    %c1 = arith.constant 1 : i32
    %c2 = arith.constant 2 : i32

    %cmp = arith.cmpi "slt", %x, %c10 : i32
    cf.cond_br %cmp, ^bb1, ^bb2

  ^bb1:
    %result1 = arith.addi %x, %c1 : i32
    cf.br ^bb3(%result1 : i32)

  ^bb2:
    %result2 = arith.muli %x, %c2 : i32
    cf.br ^bb3(%result2 : i32)

  ^bb3(%val: i32):
    func.return %val : i32
  }
}
