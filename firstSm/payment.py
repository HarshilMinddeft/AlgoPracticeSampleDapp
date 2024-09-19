from algopy import *

class SimpleDeposit(ARC4Contract):
    # State variable to track total balance
    total_balance: UInt64

    # Initialize the contract
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def createApplication(self) -> None:
        self.total_balance = UInt64(0)  # Initialize total balance to 0

    # Function to deposit a specified amount of Algos into the contract
    @arc4.abimethod(allow_actions=["NoOp"])
    def deposit(self, amount: UInt64) -> None:
        assert amount > 0, "Deposit amount must be greater than 0"
        assert Txn.amount == amount, "Amount sent does not match specified amount"

        # Update the total balance with the amount deposited
        self.total_balance += amount

    # Function to get the total balance in the contract
    @arc4.abimethod(allow_actions=["NoOp"])
    def get_total_balance(self) -> UInt64:
        return self.total_balance


# from algosdk import transaction

# # Assuming you have already set up your account and client
# amount = 1000000  # 1 Algo in microAlgos
# txn = transaction.PaymentTxn(sender, fee, suggested_params, contract_address, amount)

# # Call the deposit function
# deposit_txn = contract.call("deposit", amount)

# # Group the transactions and submit
