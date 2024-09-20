from algosdk import mnemonic
from algosdk import account as algo_account

def create_account():
    # Generate a random private key
    private_key, account_address = algo_account.generate_account()

    # Convert the private key to a mnemonic
    new_mnemonic = mnemonic.from_private_key(private_key)
    print(f"New mnemonic:=>>  {new_mnemonic}")

    # Print the account address
    print(f"Account address: {account_address}")

if __name__ == "__main__":
    create_account()
