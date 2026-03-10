module {
  // memref dialect: memory operations
  func.func @array_example() {
    %mem = memref.alloca() : memref<10xi32>
    %c5 = arith.constant 5 : index
    %c42 = arith.constant 42 : i32

    // Store value
    memref.store %c42, %mem[%c5] : memref<10xi32>

    // Load value
    %val = memref.load %mem[%c5] : memref<10xi32>

    func.return
  }

  // memref with initialization
  func.func @init_array() {
    %mem = memref.alloca() : memref<5xi32>
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c2 = arith.constant 2 : index
    %c10 = arith.constant 10 : i32
    %c20 = arith.constant 20 : i32
    %c30 = arith.constant 30 : i32

    memref.store %c10, %mem[%c0] : memref<5xi32>
    memref.store %c20, %mem[%c1] : memref<5xi32>
    memref.store %c30, %mem[%c2] : memref<5xi32>

    func.return
  }
}
