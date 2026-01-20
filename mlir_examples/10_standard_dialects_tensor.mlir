module {
  // tensor dialect: immutable tensors
  func.func @tensor_example() -> tensor<3x3xf32> {
    %t = arith.constant dense<[[1.0, 2.0, 3.0],
                                [4.0, 5.0, 6.0],
                                [7.0, 8.0, 9.0]]> : tensor<3x3xf32>
    func.return %t : tensor<3x3xf32>
  }

  // Tensor operations
  func.func @tensor_ops(%t: tensor<2x2xf32>) -> tensor<2x2xf32> {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index

    // Extract element
    %elem = tensor.extract %t[%c0, %c1] : tensor<2x2xf32>

    // Insert element
    %c99 = arith.constant 9.900000e+01 : f32
    %updated = tensor.insert %c99 into %t[%c0, %c1] : tensor<2x2xf32>

    func.return %updated : tensor<2x2xf32>
  }
}
