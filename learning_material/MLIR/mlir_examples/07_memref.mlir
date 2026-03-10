module {
  func.func @memref_example() {
    // Allocate memory
    %mem = memref.alloca() : memref<10xi32>

    // Store value
    %c5 = arith.constant 5 : index
    %c42 = arith.constant 42 : i32
    memref.store %c42, %mem[%c5] : memref<10xi32>

    // Load value
    %val = memref.load %mem[%c5] : memref<10xi32>

    func.return
  }
}
