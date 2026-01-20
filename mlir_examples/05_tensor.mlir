module {
  // Custom types: tensor
  func.func @tensor_example() -> tensor<4x4xf32> {
    %zero = arith.constant dense<0.0> : tensor<4x4xf32>
    func.return %zero : tensor<4x4xf32>
  }

  // Tensor with specific values
  func.func @tensor_init() -> tensor<2x2xf32> {
    %init = arith.constant dense<[[1.0, 2.0], [3.0, 4.0]]> : tensor<2x2xf32>
    func.return %init : tensor<2x2xf32>
  }
}
