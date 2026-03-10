module {
  // Fault-tolerant circuit with syndrome extraction
  func.func @ft_circuit() {
    %lq0 = logical_qubit.alloc {code = "surface_code", distance = 7 : i32} : !logical_qubit
    %lq1 = logical_qubit.alloc {code = "surface_code", distance = 7 : i32} : !logical_qubit

    // Apply gate
    %lq0_1 = qgate.h %lq0 {error_rate = 0.001 : f64} : !logical_qubit -> !logical_qubit

    // Entangling gate
    %lq0_2, %lq1_1 = qgate.cx %lq0_1, %lq1 {error_rate = 0.01 : f64} : !logical_qubit, !logical_qubit -> !logical_qubit, !logical_qubit

    // Extract syndrome (error correction)
    %syndrome0 = syndrome.extract %lq0_2 {code = "surface_code"} : !logical_qubit -> !syndrome
    %syndrome1 = syndrome.extract %lq1_1 {code = "surface_code"} : !logical_qubit -> !syndrome

    // Correct errors if needed
    %lq0_corrected = syndrome.correct %lq0_2, %syndrome0 : !logical_qubit, !syndrome -> !logical_qubit
    %lq1_corrected = syndrome.correct %lq1_1, %syndrome1 : !logical_qubit, !syndrome -> !logical_qubit

    func.return
  }
}
