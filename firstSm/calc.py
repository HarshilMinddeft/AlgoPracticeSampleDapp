from algopy import *

class Calculator(ARC4Contract):
    # State variable to store the last result
    last_result: UInt64

    # Initialize the contract
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def createApplication(self) -> None:
        self.last_result = UInt64(0)  # Initialize last result to 0

    # Add two numbers
    @arc4.abimethod(allow_actions=["NoOp"])
    def add(self, a: UInt64, b: UInt64) -> UInt64:
        self.last_result = a + b
        return self.last_result

    # Subtract two numbers
    @arc4.abimethod(allow_actions=["NoOp"])
    def subtract(self, a: UInt64, b: UInt64) -> UInt64:
        self.last_result = a - b
        return self.last_result

    # Multiply two numbers
    @arc4.abimethod(allow_actions=["NoOp"])
    def multiply(self, a: UInt64, b: UInt64) -> UInt64:
        self.last_result = a * b
        return self.last_result

    # Divide two numbers
    @arc4.abimethod(allow_actions=["NoOp"])
    def divide(self, a: UInt64, b: UInt64) -> UInt64:
        assert b != 0, "Cannot divide by zero"
        self.last_result = a // b  # Integer division
        return self.last_result

    # Get the last result
    @arc4.abimethod(allow_actions=["NoOp"])
    def get_last_result(self) -> UInt64:
        return self.last_result
