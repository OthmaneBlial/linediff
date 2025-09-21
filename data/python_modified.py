import os
import sys
import json
from typing import List, Dict, Optional, Union

class Calculator:
    """An enhanced calculator class with history tracking."""

    def __init__(self, initial_value: float = 0.0):
        self.value = initial_value
        self.history = []

    def add(self, x: float) -> float:
        """Add x to current value and track operation."""
        old_value = self.value
        self.value += x
        self.history.append(f"add({x}): {old_value} -> {self.value}")
        return self.value

    def subtract(self, x: float) -> float:
        """Subtract x from current value and track operation."""
        old_value = self.value
        self.value -= x
        self.history.append(f"subtract({x}): {old_value} -> {self.value}")
        return self.value

    def multiply(self, x: float) -> float:
        """Multiply current value by x and track operation."""
        old_value = self.value
        self.value *= x
        self.history.append(f"multiply({x}): {old_value} -> {self.value}")
        return self.value

    def divide(self, x: float) -> float:
        """Divide current value by x and track operation."""
        if x == 0:
            raise ValueError("Cannot divide by zero")
        old_value = self.value
        self.value /= x
        self.history.append(f"divide({x}): {old_value} -> {self.value}")
        return self.value

    def get_history(self) -> List[str]:
        """Get operation history."""
        return self.history.copy()

def fibonacci(n: int, memo: Optional[Dict[int, int]] = None) -> List[int]:
    """Generate fibonacci sequence up to n terms with memoization."""
    if memo is None:
        memo = {}

    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    sequence = [0, 1]
    for i in range(2, n):
        if i in memo:
            next_val = memo[i]
        else:
            next_val = sequence[i-1] + sequence[i-2]
            memo[i] = next_val
        sequence.append(next_val)
    return sequence

def save_to_file(data: Union[Dict, List], filename: str) -> None:
    """Save data to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    """Enhanced main function with file output."""
    calc = Calculator(10)
    print(f"Initial value: {calc.value}")

    calc.add(5)
    print(f"After adding 5: {calc.value}")

    calc.multiply(2)
    print(f"After multiplying by 2: {calc.value}")

    # Save history to file
    history_data = {"operations": calc.get_history(), "final_value": calc.value}
    save_to_file(history_data, "calc_history.json")

    fib = fibonacci(15)  # Increased from 10 to 15
    print(f"Fibonacci sequence: {fib}")

    # Save fibonacci data
    fib_data = {"sequence": fib, "length": len(fib)}
    save_to_file(fib_data, "fibonacci.json")

if __name__ == "__main__":
    main()
