from algopy import *
from algopy import arc4


# Define StreamData outside of the Steam class
class StreamData(arc4.Struct):
    streamRate: arc4.UInt64  # MicroAlgos per second
    startTime: arc4.UInt64
    endTime: arc4.UInt64  # Time when all funds will be streamed
    withdrawnAmount: arc4.UInt64
    recipient: arc4.Address  # Recipient account
    balance: arc4.UInt64  # Track contract balance for each stream
    isStreaming: arc4.Bool  # Track streaming status
    last_withdrawal_time: arc4.UInt64  # Last withdrawal time


class TSteam(ARC4Contract):
    def __init__(self) -> None:
        self.streams = BoxMap(UInt64, StreamData, key_prefix="")
        self.streamCounter = UInt64(0)

    # Start a new stream
    @arc4.abimethod(allow_actions=["NoOp"])
    def startStream(self, recipient: Account, rate: UInt64, amount: UInt64) -> None:
        assert Txn.sender == Global.creator_address, "Only creator can start a stream"
        assert rate > UInt64(0), "Stream rate must be greater than 0"
        assert amount > UInt64(0), "Stream amount must be greater than 0"

        # Increment the stream counter to get a unique stream ID
        self.streamCounter += UInt64(1)
        newStreamId = self.streamCounter

        # Calculate the stream end time: total time to stream all the amount = amount / rate
        stream_duration = amount // rate
        end_time = Global.latest_timestamp + stream_duration

        # Create a new StreamData object
        self.streams[newStreamId] = StreamData(
            streamRate=arc4.UInt64(rate),
            startTime=arc4.UInt64(Global.latest_timestamp),
            endTime=arc4.UInt64(end_time),
            withdrawnAmount=arc4.UInt64(0),
            recipient=arc4.Address(recipient),
            balance=arc4.UInt64(amount),
            isStreaming=arc4.Bool(True),
            last_withdrawal_time=arc4.UInt64(0),
        )

    # Calculate the total streamed amount for a specific stream
    @subroutine
    def _calculateStreamedAmount(self, streamId: UInt64) -> UInt64:
        # assert streamId < self.streamCounter, "Invalid stream ID"
        stream = self.streams[streamId].copy()
        current_time = Global.latest_timestamp

        if current_time >= stream.endTime:
            total_streamed = stream.balance.native + stream.withdrawnAmount.native
        else:
            elapsed_time = current_time - stream.startTime.native
            total_streamed = elapsed_time * stream.streamRate.native

        # Ensure total_streamed does not exceed initial amount
        initial_amount = stream.streamRate.native * (
            stream.endTime.native - stream.startTime.native
        )
        if total_streamed > initial_amount:
            total_streamed = initial_amount

        return total_streamed - stream.withdrawnAmount.native

    # Withdraw funds for the recipient of a specific stream
    @arc4.abimethod(allow_actions=["NoOp"])
    def withdraw(self, streamId: UInt64) -> None:
        # assert streamId < self.streamCounter, "Invalid stream ID"
        stream = self.streams[streamId].copy()
        # assert Txn.sender == stream.recipient, "Only the recipient can withdraw"

        available_amount = self._calculateStreamedAmount(streamId)
        balance = stream.balance

        if available_amount > balance:
            amount_to_withdraw = balance
        else:
            amount_to_withdraw = arc4.UInt64(available_amount)

        # assert amount_to_withdraw > arc4.UInt64(0), "No available funds to withdraw"

        # Update the stream's withdrawn amount and balance
        updated_withdrawn = stream.withdrawnAmount.native + amount_to_withdraw.native
        updated_balance = stream.balance.native - amount_to_withdraw.native
        updated_stream = StreamData(
            streamRate=stream.streamRate,
            startTime=stream.startTime,
            endTime=stream.endTime,
            withdrawnAmount=arc4.UInt64(updated_withdrawn),
            recipient=stream.recipient,
            balance=arc4.UInt64(updated_balance),
            isStreaming=stream.isStreaming,
            last_withdrawal_time=arc4.UInt64(Global.latest_timestamp),
        )

        # Update the stream data in the DynamicArray
        self.streams[streamId] = updated_stream.copy()

        # Submit inner transaction for payment
        itxn.InnerTransaction(
            sender=Global.current_application_address,
            receiver=stream.recipient.native,
            amount=amount_to_withdraw.native,
            note=b"Withdrawal from stream",
            type=TransactionType.Payment,
        ).submit()

    @arc4.abimethod(allow_actions=["NoOp"])
    def getStreamData(self, streamId: UInt64) -> StreamData:

        assert streamId <= self.streamCounter, "Invalid stream ID"

        # Retrieve the stream data
        stream_data = self.streams[streamId].copy()

        # Return the stream data
        return StreamData(
            streamRate=stream_data.streamRate,
            startTime=stream_data.startTime,
            endTime=stream_data.endTime,
            withdrawnAmount=stream_data.withdrawnAmount,
            recipient=stream_data.recipient,
            balance=stream_data.balance,
            isStreaming=stream_data.isStreaming,
            last_withdrawal_time=stream_data.last_withdrawal_time,
        )
