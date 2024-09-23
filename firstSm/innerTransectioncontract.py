from algopy import *

class SimpleDeposit(ARC4Contract):
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create_application(self) -> None:
        pass

    @arc4.abimethod(allow_actions=["NoOp"])
    def get_balance(self) -> UInt64:
        return self.get_balance()  # Fetches the contract's balance in microAlgos

    @arc4.abimethod(allow_actions=["NoOp"])
    def withdraw(self, amount: UInt64) -> None:
        # Create an inner transaction to send the funds to the caller
        itxn.InnerTransaction(
            sender=Global.current_application_address,
            fee=1000,
            receiver=Global.creator_address,
            amount=amount, 
            note=b"Withdrawal from contract",
            type=TransactionType.Payment
        ).submit()
