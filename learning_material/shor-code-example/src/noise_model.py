"""Noise models for testing Shor code error correction."""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional
from enum import IntEnum


class ErrorType(IntEnum):
    """Types of quantum errors."""
    NONE = 0
    X = 1  # Bit-flip
    Z = 2  # Phase-flip
    Y = 3  # Both (Y = iXZ, but we'll do X then Z)


class NoiseModel:
    """Noise model for injecting errors into quantum states."""
    
    def __init__(self, error_rate: float = 0.1, seed: Optional[int] = None):
        """
        Initialize noise model.
        
        Args:
            error_rate: Probability of an error occurring on each qubit
            seed: Random seed for reproducibility
        """
        self.error_rate = error_rate
        self.rng = np.random.RandomState(seed)
    
    def apply_error(
        self, 
        state: np.ndarray, 
        qubit: int, 
        error_type: ErrorType,
        n_qubits: int = 9
    ) -> np.ndarray:
        """
        Apply a specific error to a qubit in the statevector.
        
        Args:
            state: Quantum statevector
            qubit: Index of qubit to apply error to (0-8)
            error_type: Type of error to apply
            n_qubits: Total number of qubits
            
        Returns:
            Modified statevector
        """
        I = np.eye(2, dtype=complex)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        
        def kron_n(*ops):
            out = ops[0]
            for op in ops[1:]:
                out = np.kron(out, op)
            return out
        
        ops = [I] * n_qubits
        
        if error_type == ErrorType.X:
            ops[qubit] = X
        elif error_type == ErrorType.Z:
            ops[qubit] = Z
        elif error_type == ErrorType.Y:
            # Y = iXZ, but we'll apply X then Z (up to phase)
            ops[qubit] = Z @ X
        else:  # ErrorType.NONE
            return state
        
        U = kron_n(*ops)
        return U @ state
    
    def apply_random_errors(
        self,
        state: np.ndarray,
        n_qubits: int = 9,
        max_errors: Optional[int] = None
    ) -> Tuple[np.ndarray, List[Tuple[int, ErrorType]]]:
        """
        Apply random errors according to the noise model.
        
        Args:
            state: Quantum statevector
            n_qubits: Total number of qubits
            max_errors: Maximum number of errors to apply (None = no limit)
            
        Returns:
            Tuple of (modified statevector, list of (qubit, error_type) applied)
        """
        errors_applied = []
        modified_state = state.copy()
        
        for q in range(n_qubits):
            if max_errors is not None and len(errors_applied) >= max_errors:
                break
            
            if self.rng.random() < self.error_rate:
                # Randomly choose error type (X, Z, or Y)
                error_type = ErrorType(self.rng.randint(1, 4))
                modified_state = self.apply_error(modified_state, q, error_type, n_qubits)
                errors_applied.append((q, error_type))
        
        return modified_state, errors_applied
    
    def apply_single_error(
        self,
        state: np.ndarray,
        qubit: int,
        error_type: ErrorType = ErrorType.X,
        n_qubits: int = 9
    ) -> np.ndarray:
        """
        Apply a single error to a specific qubit (deterministic).
        
        Args:
            state: Quantum statevector
            qubit: Index of qubit to apply error to
            error_type: Type of error to apply
            n_qubits: Total number of qubits
            
        Returns:
            Modified statevector
        """
        return self.apply_error(state, qubit, error_type, n_qubits)


class DepolarizingNoise(NoiseModel):
    """Depolarizing noise model - each qubit independently depolarizes."""
    
    def __init__(self, depolarizing_rate: float = 0.1, seed: Optional[int] = None):
        """
        Initialize depolarizing noise model.
        
        Args:
            depolarizing_rate: Probability that a qubit depolarizes
            seed: Random seed for reproducibility
        """
        super().__init__(error_rate=depolarizing_rate, seed=seed)
        self.depolarizing_rate = depolarizing_rate
    
    def apply_random_errors(
        self,
        state: np.ndarray,
        n_qubits: int = 9,
        max_errors: Optional[int] = None
    ) -> Tuple[np.ndarray, List[Tuple[int, ErrorType]]]:
        """
        Apply depolarizing noise: each qubit independently has probability p
        of being replaced by a completely mixed state (X, Y, or Z with equal prob).
        """
        errors_applied = []
        modified_state = state.copy()
        
        for q in range(n_qubits):
            if max_errors is not None and len(errors_applied) >= max_errors:
                break
            
            if self.rng.random() < self.depolarizing_rate:
                # In depolarizing channel, X, Y, Z each with prob p/3
                # We'll randomly choose one
                error_type = ErrorType(self.rng.randint(1, 4))
                modified_state = self.apply_error(modified_state, q, error_type, n_qubits)
                errors_applied.append((q, error_type))
        
        return modified_state, errors_applied

