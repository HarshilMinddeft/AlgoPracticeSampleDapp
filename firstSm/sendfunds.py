from algosdk.v2client import algod
from algosdk import account, transaction, mnemonic, encoding

# Define your Algod client connection parameters
ALGOD_URL = "http://localhost:4001"  # Or use your DappFlow localnet URL
ALGOD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  # Replace with the actual token from DappFlow

# Replace with your App ID
APP_ID = 1010

# Create an Algod client
algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)

# Your mnemonic of the account that will send Algos
MNEMONIC = "pig jewel orange glass crowd unlock debris build family soul extra abstract prosper double jaguar cotton small clog because sell promote kind tip able velvet"

def get_contract_address(app_id):
    # Convert app_id to bytes and generate address
    app_id_bytes = app_id.to_bytes(8, 'big')  # 8 bytes for app ID
    return encoding.encode_address(encoding.checksum(b"\x01" + app_id_bytes))  # Prefix with 0x01

def transfer_algos_to_contract():
    # Get the private key from the mnemonic
    private_key = mnemonic.to_private_key(MNEMONIC)
    # Get the sender account address from the private key
    sender_address = account.address_from_private_key(private_key)

    # Calculate the contract address from the application ID
    contract_address = get_contract_address(APP_ID)
    print(f"Contract Address: {contract_address}")

    # Fetch the suggested transaction parameters
    params = algod_client.suggested_params()

    # Define the amount to send (in microAlgos; 1 Algo = 1,000,000 microAlgos)
    amount = 1000000  # 1 Algo

    # Create the payment transaction to send Algos to the contract address
    txn = transaction.PaymentTxn(
        sender=sender_address,
        sp=params,
        receiver=contract_address,
        amt=amount
    )

    # Sign the transaction
    signed_txn = txn.sign(private_key)

    # Send the transaction
    txid = algod_client.send_transaction(signed_txn)

    # Wait for confirmation
    try:
        confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 4)
        print("Transaction confirmed in round", confirmed_txn['confirmed-round'])
        print(f"Sent {amount} microAlgos to contract with App ID {APP_ID}")
    except Exception as e:
        print(f"Failed to send transaction: {e}")

if __name__ == "__main__":
    transfer_algos_to_contract()
