from algopy import *

# from algopy.arc4 import abimethod


# ARC4Contract is algorand standard it make contract more intractable, automatically handel routes
class Firstsm(ARC4Contract):
    # @abimethod()
    # These two types are set to globel types
    asset_id: UInt64
    unitary_price: UInt64

    # create the app
    # This abimethode is used for call contract user can call this function
    # we used create = "required" this will call this function with contract creation
    #  NoOp (general operation) transaction, meaning it's not a special type of action like creating, deleting, or updating the application.
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    # This function is for creating contract
    def createApplication(self, asset_id: Asset, unitary_price: UInt64) -> None:
        self.asset_id = asset_id.id
        self.unitary_price = unitary_price

    # update the listing price.
    @arc4.abimethod
    # This function is for updating the asset price.
    def setPrice(self, unitary_price: UInt64) -> None:
        # check is for onlyOwner can call this external function.
        assert Txn.sender == Global.creator_address
        self.unitary_price = unitary_price

    # opt into the asset that will be sold
    # This function is for to check smartcontract account should be optend in to the asset that seller wanted to sell
    @arc4.abimethod
    def opt_in_to_asset(self, mbrPay: gtxn.PaymentTransaction) -> None:
        assert Txn.sender == Global.creator_address
        assert not Global.current_application_address.is_opted_in(Asset(self.asset_id))

        assert mbrPay.receiver == Global.current_application_address
        assert mbrPay.amount == Global.min_balance + Global.asset_opt_in_min_balance
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
        ).submit()

    # buy the asset
    @arc4.abimethod
    def buy(
        self,
        buyerTxn: gtxn.PaymentTransaction,
        quantity: UInt64,
    ) -> None:
        # check for buyer is buying asset at price that seller decided, not giving free stuff
        assert self.unitary_price != UInt64(0)
        decoded_quantity = quantity
        # check for account that call buy method is same that sent paymentTransection
        assert buyerTxn.sender == Txn.sender

        assert buyerTxn.receiver == Global.current_application_address
        assert buyerTxn.amount == self.unitary_price * decoded_quantity
        # for sending asset
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Txn.sender,
            asset_amount=decoded_quantity,
        ).submit()

    # delete the application
    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def deleteApplication(self) -> None:
        assert Txn.sender == Global.creator_address

        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Global.creator_address,
            asset_amount=0,
            asset_close_to=Global.creator_address,
        ).submit()

        itxn.Payment(
            receiver=Global.creator_address,
            amount=0,
            close_remainder_to=Global.creator_address,
        ).submit()
