module {
  // Attributes: compile-time constants
  func.func @attribute_example() {
    // Operation name is an attribute
    %c1 = arith.constant 1 : i32  // "arith.constant" and "1" are attributes

    // Comparison predicate is an attribute
    %cmp = arith.cmpi "eq", %c1, %c1 : i32  // "eq" is an attribute

    // String attributes
    %c5 = arith.constant 5 : i32
    %cmp_lt = arith.cmpi "slt", %c1, %c5 : i32  // "slt" (signed less than) is an attribute

    func.return
  }
}
