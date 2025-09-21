import os
import sys
from typing import List, Dict, Optional

class Calculator:
    """A simple calculator class."""

    def __init__(self, initial_value: float = 0.0):
        self.value = initial_value

    def add(self, x: float) -> float:
        """Add x to current value."""
        self.value += x
        return self.value

    def subtract(self, x: float) -> float:
        """Subtract x from current value."""
        self.value -= x
        return self.value

    def multiply(self, x: float) -> float:
        """Multiply current value by x."""
        self.value *= x
        return self.value

    def divide(self, x: float) -> float:
        """Divide current value by x."""
        if x == 0:
            raise ValueError("Cannot divide by zero")
        self.value /= x
        return self.value

def fibonacci(n: int) -> List[int]:
    """Generate fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence

def main():
    """Main function."""
    calc = Calculator(10)
    print(f"Initial value: {calc.value}")

    calc.add(5)
    print(f"After adding 5: {calc.value}")

    calc.multiply(2)
    print(f"After multiplying by 2: {calc.value}")

    fib = fibonacci(10)
    print(f"Fibonacci sequence: {fib}")

if __name__ == "__main__":
    main()
