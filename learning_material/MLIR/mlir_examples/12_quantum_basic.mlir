module {
  // Hypothetical qgate dialect operations
  func.func @quantum_circuit() {
    // Allocate logical qubits
    %q0 = logical_qubit.alloc {code = "surface_code", distance = 5 : i32} : !logical_qubit
    %q1 = logical_qubit.alloc {code = "surface_code", distance = 5 : i32} : !logical_qubit

    // Apply quantum gates (with error rates as attributes)
    %q0_1 = qgate.h %q0 {error_rate = 0.001 : f64} : !qubit -> !qubit
    %q1_1 = qgate.h %q1 {error_rate = 0.001 : f64} : !qubit -> !qubit

    // Entangling gate
    %q0_2, %q1_2 = qgate.cx %q0_1, %q1_1 {error_rate = 0.01 : f64} : !qubit, !qubit -> !qubit, !qubit

    // Measure
    %result = qgate.measure %q0_2 : !qubit -> i1

    logical_qubit.dealloc %q0_2 : !logical_qubit
    logical_qubit.dealloc %q1_2 : !logical_qubit

    func.return
  }
}
