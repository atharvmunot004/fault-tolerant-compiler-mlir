module {
  // Built-in types
  func.func @example_types() {
    // Integer types
    %c5 = arith.constant 5 : i32
    %c10 = arith.constant 10 : i64

    // Floating-point types
    %fval = arith.constant 3.140000e+00 : f32
    %fval64 = arith.constant 3.140000e+00 : f64

    // Index type (platform-dependent)
    %idx = arith.constant 0 : index

    func.return
  }
}
