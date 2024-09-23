import pytest
from algokit_utils import get_localnet_default_account
from algokit_utils.config import config
from algosdk import error
from algokit_utils.beta.algorand_client import AlgorandClient, PayParams
from algokit_utils.beta.account_manager import AddressAndSigner
from smart_contracts.artifacts.firstsm.simple_deposit_client import SimpleDepositClient

@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    """Get an Algorand client."""
    return AlgorandClient.default_local_net()

@pytest.fixture(scope="session")
def dispenser(algorand: AlgorandClient) -> AddressAndSigner:
    """Get the dispenser account with test tokens."""
    return algorand.account.dispenser()

@pytest.fixture(scope="session")
def creator(algorand: AlgorandClient, dispenser: AddressAndSigner) -> AddressAndSigner:
    """Create an account and fund it with some tokens from the dispenser."""
    acct = algorand.account.random()
    algorand.send.payment(
        PayParams(sender=dispenser.address, receiver=acct.address, amount=10_000_000)
    )
    return acct

@pytest.fixture(scope="session")
def simple_deposit_client(algorand: AlgorandClient, creator: AddressAndSigner) -> SimpleDepositClient:
    """Deploy the SimpleDeposit contract for use in tests."""
    client = SimpleDepositClient(
        algod_client=algorand.client.algod,
        sender=creator.address,
        signer=creator.signer,
    )
    client.create_create_application()  # Deploy the contract
    return client

def test_send_and_get_balance(  
    simple_deposit_client: SimpleDepositClient,
    creator: AddressAndSigner,
    algorand: AlgorandClient,
):
    # Step 1: Send test Algos to the contract
    transfer_amount = 1_001_000  # 1 Algo
    print(f"Sending {transfer_amount} microAlgos to contract...")

    algorand.send.payment(
        PayParams(sender=creator.address, receiver=simple_deposit_client.app_address, amount=transfer_amount)
    )
    print("Algos Sent")

    # Step 2: Get the contract's balance directly
    account_info = algorand.client.algod.account_info(simple_deposit_client.app_address)
    balance = account_info['amount']  # This fetches the balance in microAlgos
    print(f"Contract balance: {balance} microAlgos")
    
    # # Step 3: Withdraw Algos from the contract
    withdraw_amount = 1_000_000
    print(f"Withdrawing {withdraw_amount} microAlgos from contract...")
    simple_deposit_client.withdraw(amount=withdraw_amount)
    print("RemovedFunds-----")
    # Step 4: Check the contract's balance after withdrawal
    account_info = algorand.client.algod.account_info(simple_deposit_client.app_address)
    balance_after_withdrawal = account_info['amount']  # This fetches the balance in microAlgos
    print(f"Contract balance after withdraw: {balance_after_withdrawal} microAlgos")
