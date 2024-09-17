import algokit_utils
import pytest
from algokit_utils import get_localnet_default_account
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algopy import *
from algosdk.v2client.indexer import IndexerClient
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
    PayParams,
    AssetCreateParams,
    AssetOptInParams,
    AssetTransferParams,
)
from algokit_utils.beta.account_manager import AddressAndSigner
import algosdk
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.firstsm.firstsm_client import FirstsmClient


# scope session means it needs to run once though it have multiple files tests
@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    """Get and algorandClient"""
    return AlgorandClient.default_local_net()


@pytest.fixture(scope="session")
def dispenser(algorand: AlgorandClient) -> AddressAndSigner:
    """Get dispenser account tokens"""
    return algorand.account.dispenser()


@pytest.fixture(scope="session")
def creator(algorand: AlgorandClient, dispenser: AddressAndSigner) -> AddressAndSigner:
    acct = algorand.account.random()

    algorand.send.payment(
        PayParams(sender=dispenser.address, receiver=acct.address, amount=10_000_000)
    )
    return acct


@pytest.fixture(scope="session")
def test_asset_id(creator: AddressAndSigner, algorand: AlgorandClient) -> int:
    sent_txn = algorand.send.asset_create(
        AssetCreateParams(sender=creator.address, total=10)
    )
    print(sent_txn)
    return sent_txn["confirmation"]["asset-index"]


@pytest.fixture(scope="session")
def digital_marketplace_client(
    algorand: AlgorandClient, creator: AddressAndSigner, test_asset_id: int
) -> FirstsmClient:
    """Iniciate application for using for our tests"""
    client = FirstsmClient(
        algod_client=algorand.client.algod,
        sender=creator.address,
        signer=creator.signer,
    )
    client.create_create_application(unitary_price=0, asset_id=test_asset_id)
    return client


def test_opt_in_to_asset(
    digital_marketplace_client: FirstsmClient,
    creator: AddressAndSigner,
    test_asset_id: int,
    algorand: AlgorandClient,
):
    # Ensure get_asset_information throws an error because app is not yet opted in
    pytest.raises(
        algosdk.error.AlgodHTTPError,
        lambda: algorand.account.get_asset_information(
            digital_marketplace_client.app_address, test_asset_id
        ),
    )

    # Opt in to asset
    mbr_pay_txn = algorand.transactions.payment(
        PayParams(
            sender=creator.address,
            receiver=digital_marketplace_client.app_address,
            amount=200_000,
            extra_fee=1_000,
        )
    )
    result = digital_marketplace_client.opt_in_to_asset(
        mbrPay=TransactionWithSigner(txn=mbr_pay_txn, signer=creator.signer),
        transaction_parameters=algokit_utils.TransactionParameters(
            foreign_assets=[test_asset_id]
        ),
    )
    assert result.confirmed_round

    # Confirm that the application address now holds 0 of the asset
    assert (
        algorand.account.get_asset_information(
            digital_marketplace_client.app_address, test_asset_id
        )["asset-holding"]["amount"]
        == 0
    )


def test_set_price(digital_marketplace_client: FirstsmClient):
    result = digital_marketplace_client.set_price(unitary_price=3_00_000)
    assert result.confirmed_round


def test_deposit(
    digital_marketplace_client: FirstsmClient,
    creator: AddressAndSigner,
    test_asset_id: int,
    algorand: AlgorandClient,
):
    result = algorand.send.asset_transfer(
        AssetTransferParams(
            sender=creator.address,
            receiver=digital_marketplace_client.app_address,
            asset_id=test_asset_id,
            amount=3,
        )
    )
    assert result["confirmation"]
    assert (
        algorand.account.get_asset_information(
            digital_marketplace_client.app_address, test_asset_id
        )["asset-holding"]["amount"]
        == 3
    )


def test_buy(
    digital_marketplace_client: FirstsmClient,
    creator: AddressAndSigner,
    test_asset_id: int,
    algorand: AlgorandClient,
    dispenser: AddressAndSigner,
):
    # Set the price before attempting to buy
    result = digital_marketplace_client.set_price(unitary_price=3_00_000)
    assert result.confirmed_round

    # for creation of new buyer
    buyer = algorand.account.random()

    # use the dispenser to fund buyer
    algorand.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=buyer.address,
            amount=10_000_000,
        )
    )
    # opt the buyer into asset
    algorand.send.asset_opt_in(
        AssetOptInParams(sender=buyer.address, asset_id=test_asset_id)
    )

    # form a transection for buying two asset (2*3_000_000)
    buyer_payment_txn = algorand.transactions.payment(
        PayParams(
            sender=buyer.address,
            receiver=digital_marketplace_client.app_address,
            amount=2 * 3_300_000,
            extra_fee=1_000,
        )
    )

    result = digital_marketplace_client.buy(
        buyerTxn=TransactionWithSigner(txn=buyer_payment_txn, signer=buyer.signer),
        quantity=2,
        transaction_parameters=algokit_utils.TransactionParameters(
            sender=buyer.address,
            signer=buyer.signer,
            # for telling evm about asset call
            foreign_assets=[test_asset_id],
        ),
    )

    assert result.confirmed_round
    assert (
        algorand.account.get_asset_information(buyer.address, test_asset_id)[
            "asset-holding"
        ]["amount"]
        == 2
    )


def test_delete_application(
    digital_marketplace_client: FirstsmClient,
    creator: AddressAndSigner,
    test_asset_id: int,
    algorand: AlgorandClient,
    dispenser: AddressAndSigner,
):
    before_call_amount = algorand.account.get_information(creator.address)["amount"]

    result = digital_marketplace_client.delete_delete_application(
        transaction_parameters=algokit_utils.TransactionParameters(
            foreign_assets=[test_asset_id],
        )
    )
    assert result.confirmed_round

    after_call_amount = algorand.account.get_information(creator.address)["amount"]

    assert after_call_amount - before_call_amount == (2 * 3_300_000) + 200_000 - 3_000
    assert (
        algorand.account.get_asset_information(creator.address, test_asset_id)[
            "asset-holding"
        ]["amount"]
        == 8
    )
