import http.server
import socketserver
import threading
import sys
import sqlite3
from urllib.parse import urlparse, parse_qs
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound
import json # For parsing ABI

# --- Configuration for Smart Contract Interaction ---
# !!! IMPORTANT: Replace with your actual blockchain details !!!
# Updated Web3 Provider URL to Sepolia public node
WEB3_PROVIDER_URL = "https://ethereum-sepolia-rpc.publicnode.com"
REPUTATION_CONTRACT_ADDRESS = "0xYourDeployedContractAddressHere"  # Example: "0x123...abc"
OWNER_PRIVATE_KEY = "0xYourOwnerPrivateKeyHere"  # !!! DANGER: NEVER HARDCODE IN PRODUCTION !!!
# You need the ABI JSON string. Get this from your contract compilation output.
REPUTATION_CONTRACT_ABI = json.loads('''
[
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_creator",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "_referrerReputation",
                "type": "address"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "name": "allUsers",
        "outputs": [
            {
                "internalType": "string",
                "name": "username",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "salt",
                "type": "string"
            },
            {
                "internalType": "bytes32",
                "name": "passwordHash",
                "type": "bytes32"
            },
            {
                "internalType": "uint256",
                "name": "downloadSize",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "uploadSize",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_username",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_salt",
                "type": "string"
            },
            {
                "internalType": "bytes32",
                "name": "_passwordHash",
                "type": "bytes32"
            },
            {
                "internalType": "uint256",
                "name": "_downloadSize",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "_uploadSize",
                "type": "uint256"
            }
        ],
        "name": "addUser",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getOffchainDataUrl",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_username",
                "type": "string"
            }
        ],
        "name": "getUserData",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "string",
                        "name": "username",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "salt",
                        "type": "string"
                    },
                    {
                        "internalType": "bytes32",
                        "name": "passwordHash",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "uint256",
                        "name": "downloadSize",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "uploadSize",
                        "type": "uint256"
                    }
                ],
                "internalType": "struct Reputation.UserData",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_username",
                "type": "string"
            }
        ],
        "name": "migrateUserData",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "offchainDataUrl",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "referrerReputation",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_offchainDataUrl",
                "type": "string"
            }
        ],
        "name": "setOffchainDataUrl",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_username",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "_downloadSize",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "_uploadSize",
                "type": "uint256"
            }
        ],
        "name": "updateUser",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
''') # End of ABI
# --- End Smart Contract Configuration ---

# Define the port to listen on.
PORT = 8091

# Global Web3 instances (initialized once at server startup)
w3_instance = None
reputation_contract = None
owner_eth_account = None

def initialize_web3_contract(provider_url, contract_address, contract_abi, private_key):
    """
    Initializes Web3 connection and returns contract instance and owner account.
    """
    try:
        w3 = Web3(HTTPProvider(provider_url))
        if not w3.is_connected():
            sys.stderr.write(f"Error: Not connected to Web3 provider at {provider_url}\n")
            return None, None, None

        contract_address_checksum = w3.to_checksum_address(contract_address)
        contract = w3.eth.contract(address=contract_address_checksum, abi=contract_abi)

        owner_account = w3.eth.account.from_key(private_key)
        sys.stdout.write(f"Connected to Web3. Owner account: {owner_account.address}\n")
        return w3, contract, owner_account
    except Exception as e:
        sys.stderr.write(f"Error initializing Web3 or contract: {e}\n")
        return None, None, None

def update_smart_contract_reputation(username, new_download_size, new_upload_size):
    """
    Calls the updateUser function on the smart contract, but only if the new
    download or upload size is greater than the current on-chain value.
    """
    global w3_instance, reputation_contract, owner_eth_account

    if not (w3_instance and reputation_contract and owner_eth_account):
        sys.stderr.write("Smart contract interaction not initialized or failed. Skipping update.\n")
        return

    try:
        # 1. Get current user data from the smart contract
        # getUserData returns a tuple: (username, salt, passwordHash, downloadSize, uploadSize)
        try:
            current_user_data = reputation_contract.functions.getUserData(username).call()
            on_chain_password_hash = current_user_data[2]
            on_chain_download_size = current_user_data[3]
            on_chain_upload_size = current_user_data[4]

            # Check if user exists on contract (passwordHash is not bytes32(0))
            # Bytes32(0) in Solidity is a byte string of 32 null bytes in Python
            user_exists_on_chain = on_chain_password_hash != b'\x00' * 32

            sys.stdout.write(f"User '{username}' on-chain stats: Download={on_chain_download_size}, Upload={on_chain_upload_size}\n")

        except Exception as e:
            sys.stderr.write(f"Error getting current user data for '{username}' from contract: {e}. Assuming user not found or call failed.\n")
            user_exists_on_chain = False
            on_chain_download_size = 0 # Assume zero if unable to retrieve
            on_chain_upload_size = 0   # Assume zero if unable to retrieve

        # If user doesn't exist on contract, we cannot call updateUser (it will revert anyway if called)
        if not user_exists_on_chain:
            sys.stdout.write(f"User '{username}' does not exist on smart contract. Skipping updateUser. Consider calling addUser first if this is a new user.\n")
            return

        # 2. Compare values
        update_needed = False
        if new_download_size > on_chain_download_size:
            sys.stdout.write(f"New download size {new_download_size} > on-chain download size {on_chain_download_size}. Update needed.\n")
            update_needed = True
        if new_upload_size > on_chain_upload_size:
            sys.stdout.write(f"New upload size {new_upload_size} > on-chain upload size {on_chain_upload_size}. Update needed.\n")
            update_needed = True

        if not update_needed:
            sys.stdout.write(f"No increase in download/upload for user '{username}'. Skipping smart contract update.\n")
            return

        # 3. Proceed with update if needed
        sys.stdout.write(f"Initiating update for user '{username}' on smart contract...\n")
        transaction = reputation_contract.functions.updateUser(
            username,
            new_download_size,
            new_upload_size
        ).build_transaction({
            'chainId': w3_instance.eth.chain_id,
            'from': owner_eth_account.address,
            'nonce': w3_instance.eth.get_transaction_count(owner_eth_account.address),
            'gasPrice': w3_instance.eth.gas_price,
            'gas': 2000000 # Adjust gas limit as needed.
        })

        signed_txn = w3_instance.eth.account.sign_transaction(transaction, private_key=owner_eth_account.key)
        tx_hash = w3_instance.eth.send_raw_transaction(signed_txn.rawTransaction)
        sys.stdout.write(f"Sent transaction to update user '{username}': {tx_hash.hex()}\n")

        tx_receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        sys.stdout.write(f"Transaction receipt for '{username}': Status={tx_receipt.status}, Block={tx_receipt.blockNumber}\n")

        if tx_receipt.status == 1:
            sys.stdout.write(f"Successfully updated user '{username}' on smart contract.\n")
        else:
            sys.stderr.write(f"Transaction for user '{username}' failed on smart contract (status 0).\n")

    except ValueError as ve:
        sys.stderr.write(f"Error building transaction for user '{username}': {ve}\n")
    except TransactionNotFound as e:
        sys.stderr.write(f"Transaction for user '{username}' not found on chain (possibly dropped or timed out): {e}\n")
    except Exception as e:
        sys.stderr.write(f"Unhandled error interacting with smart contract for user '{username}': {e}\n")


# --- SQLite Database Helper ---
def query_sqlite_db(db_path, query):
    """
    Connects to a SQLite database, executes a query, and returns the results
    as a list of dictionaries, where each dictionary represents a row
    with column names as keys.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        column_names = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        result_dicts = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = row[i]
            result_dicts.append(row_dict)
        return result_dicts
    except sqlite3.Error as e:
        sys.stderr.write(f"SQLite error during key loading: {e}\n")
        return []
    except FileNotFoundError:
        sys.stderr.write(f"Error: Database file not found at {db_path}\n")
        return []
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred during key loading: {e}\n")
        return []
    finally:
        if conn:
            conn.close()

# --- Custom ThreadingTCPServer to pass shared data ---
class CustomThreadingTCPServer(socketserver.ThreadingTCPServer):
    """
    A custom ThreadingTCPServer that allows passing shared data
    (like the pre-loaded keys map and torrents dictionary) to each handler instance.
    """
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, shared_data=None):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)
        self.shared_data = shared_data if shared_data is not None else {}

# --- Custom Request Handler ---
class RequestLoggerHandler(http.server.SimpleHTTPRequestHandler):
    """
    A custom HTTP request handler that logs details of incoming requests
    to standard output (stdout).
    """
    def __init__(self, request, client_address, server):
        # Access shared data from the server instance
        self.torrents = server.shared_data.get('torrents', {})
        self.keys = server.shared_data.get('keys', {})
        self.user_stats = server.shared_data.get('user_stats', {})
        super().__init__(request, client_address, server)

    def log_message(self, format, *args):
        """
        Overrides the default log_message to ensure logs go to stdout
        and include a timestamp.
        """
        try:
            sys.stdout.write("%s - - [%s] %s\n" %
                             (self.address_string(),
                              self.log_date_time_string(),
                              format % args))
        except Exception: # Catch any error during logging to prevent server crash
            pass

    def do_GET(self):
        """Handle GET requests."""
        self.log_request_details("GET")

        original_uri = self.headers.get('X-Original-URI')

        if original_uri:
            self.log_message("--- Original Request Details (from X-Original-URI) ---")
            parsed_original_url = urlparse(original_uri)
            original_path_segments = parsed_original_url.path.split('/')

            original_announce_id = None
            if len(original_path_segments) >= 3 and original_path_segments[1] == 'announce':
                original_announce_id = original_path_segments[2]
                self.log_message("Original Announce ID (X): %s", original_announce_id)

                params = parse_qs(parsed_original_url.query)
                self.process_and_log_announce_params(params, auth_key=original_announce_id)
                self.log_message("----------------------------------------------")
            else:
                self.log_message("Original Path: %s (not an /announce/X format)", original_path_segments)
                self.log_message("----------------------------------------------")
        else:
            self.log_message("X-Original-URI header not found. Proceeding with current request path.")
            parsed_url = urlparse(self.path)
            path_segments = parsed_url.path.split('/')

            if len(path_segments) >= 3 and path_segments[1] == 'announce':
                announce_id = path_segments[2]
                self.log_message("--- Announce Request Details (from current path) ---")
                self.log_message("Announce ID (X): %s", announce_id)
                
                params = parse_qs(parsed_url.query)
                auth_key = params.get('key', [None])[0] # Get auth_key from current path params
                self.process_and_log_announce_params(params, auth_key=auth_key)
                self.log_message("--------------------------------------------------")
            else:
                self.log_message("No specific announce parameters found in current path %s", self.path)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response_message = f"<html><body><h1>Request Received!</h1><p>Method: GET</p><p>Path: {self.path}</p></body></html>"
        self.wfile.write(response_message.encode('utf-8'))

    def process_and_log_announce_params(self, params, auth_key):
        """
        Helper function to extract, log, and update internal state for announce parameters.
        Also calls smart contract to update user reputation.
        """
        info_hash_val = params.get('info_hash', [None])[0]
        peer_id_val = params.get('peer_id', [None])[0]
        port_val = params.get('port', [None])[0]
        uploaded_val_str = params.get('uploaded', [None])[0]
        downloaded_val_str = params.get('downloaded', [None])[0]
        left_val = params.get('left', [None])[0]
        corrupt_val = params.get('corrupt', [None])[0]
        # auth_key already passed in for clarity
        numwant_val = params.get('numwant', [None])[0]
        compact_val = params.get('compact', [None])[0]
        no_peer_id_val = params.get('no_peer_id', [None])[0]
        supportcrypto_val = params.get('supportcrypto', [None])[0]
        redundant_val = params.get('redundant', [None])[0]
        ip_val = params.get('ip', [None])[0]
        ipv6_val = params.get('ipv6', [None])[0]
        event_val = params.get('event', [None])[0]

        # Convert uploaded/downloaded to int, default to 0 if None or conversion fails
        uploaded_val = int(uploaded_val_str) if uploaded_val_str is not None else 0
        downloaded_val = int(downloaded_val_str) if downloaded_val_str is not None else 0

        # Update torrents dictionary (thread-safe operations on its own dict)
        if info_hash_val and auth_key:
            if info_hash_val not in self.torrents:
                self.torrents[info_hash_val] = {}
            if auth_key not in self.torrents[info_hash_val]:
                self.torrents[info_hash_val][auth_key] = {'uploaded': 0, 'downloaded': 0}

            # Only update if new value is greater or on first seen
            if self.torrents[info_hash_val][auth_key]['uploaded'] < uploaded_val:
                 self.torrents[info_hash_val][auth_key]['uploaded'] = uploaded_val
            if self.torrents[info_hash_val][auth_key]['downloaded'] < downloaded_val:
                self.torrents[info_hash_val][auth_key]['downloaded'] = downloaded_val

        # Log parameters
        self.log_message("  Info Hash: %s", info_hash_val)
        self.log_message("  Peer ID: %s", peer_id_val)
        self.log_message("  Port: %s", port_val)
        self.log_message("  Left: %s", left_val)
        self.log_message("  Event: %s", event_val)
        self.log_message("  Key (Passkey): %s", auth_key)
        self.log_message("  Client IP: %s", ip_val)
        self.log_message("  Client IPv6: %s", ipv6_val)
        self.log_message("  Compact: %s", compact_val)
        self.log_message("  Num Want: %s", numwant_val)
        self.log_message("  Corrupt: %s", corrupt_val)
        self.log_message("  No Peer ID: %s", no_peer_id_val)
        self.log_message("  Support Crypto: %s", supportcrypto_val)
        self.log_message("  Redundant: %s", redundant_val)

        # Update user_stats and trigger smart contract update
        if auth_key is not None:
            username = self.keys.get(auth_key) # Get username from the pre-loaded keys map
            if username is not None:
                # Initialize user_stats entry if it doesn't exist
                if auth_key not in self.user_stats:
                    self.user_stats[auth_key] = {'uploaded': 0, 'downloaded': 0}

                # Update overall user stats only if the reported values are higher
                # This assumes cumulative sum from the client. Adjust logic if client sends diffs.
                if self.user_stats[auth_key]['uploaded'] < uploaded_val:
                    self.user_stats[auth_key]['uploaded'] = uploaded_val # Assuming client sends cumulative
                if self.user_stats[auth_key]['downloaded'] < downloaded_val:
                    self.user_stats[auth_key]['downloaded'] = downloaded_val # Assuming client sends cumulative

                self.log_message("-----------------------")
                self.log_message(f"Auth Key '{auth_key}' is belonging to user: {username}")
                self.log_message(f"  User {username} reporting Uploaded: {uploaded_val}, Downloaded: {downloaded_val} for torrent {info_hash_val}")
                self.log_message(f"  User {username} reporting Uploaded: {self.user_stats[auth_key]['uploaded']}, Downloaded: {self.user_stats[auth_key]['downloaded']} overall")
                self.log_message("-----------------------")

                # --- Call Smart Contract Function ---
                # Pass the username and the CUMULATIVE uploaded/downloaded stats
                update_smart_contract_reputation(
                    username,
                    self.user_stats[auth_key]['downloaded'], # downloadSize for contract
                    self.user_stats[auth_key]['uploaded']    # uploadSize for contract
                )
                # --- End Smart Contract Call ---

            else:
                self.log_message(f"-----------------------")
                self.log_message(f"Warning: Auth Key '{auth_key}' does not belong to a known user. Skipping smart contract update.")
                self.log_message("-----------------------")
        else:
            self.log_message("Warning: Auth Key (Passkey) not provided in request. Skipping smart contract update.")

    def do_POST(self):
        """Handle POST requests."""
        self.log_request_details("POST")
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length).decode('utf-8', errors='ignore')
        self.log_message("Request Body:\n%s", post_body)

        parsed_url = urlparse(self.path)
        path_segments = parsed_url.path.split('/')

        if len(path_segments) >= 3 and path_segments[1] == 'announce':
            announce_id = path_segments[2]
            self.log_message("--- Announce Request Details (POST) ---")
            self.log_message("Announce ID (X): %s", announce_id)

            params = parse_qs(parsed_url.query)
            auth_key = params.get('key', [None])[0]
            self.process_and_log_announce_params(params, auth_key=auth_key)
            self.log_message("-------------------------------------")
        elif parsed_url.query:
            self.log_message("Query Parameters (from POST URL):")
            for key, values in parse_qs(parsed_url.query).items():
                self.log_message("  %s: %s", key, ', '.join(values))

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response_message = f"<html><body><h1>Request Received!</h1><p>Method: POST</p><p>Path: {self.path}</p><p>Body: {post_body}</p></body></html>"
        self.wfile.write(response_message.encode('utf-8'))

    def do_HEAD(self):
        """Handle HEAD requests."""
        self.log_request_details("HEAD")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_PUT(self):
        """Handle PUT requests."""
        self.log_request_details("PUT")
        content_length = int(self.headers.get('Content-Length', 0))
        put_body = self.rfile.read(content_length).decode('utf-8', errors='ignore')
        self.log_message("Request Body (PUT):\n%s", put_body)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("<html><body><h1>PUT Request Received!</h1></body></html>".encode('utf-8'))

    def do_DELETE(self):
        """Handle DELETE requests."""
        self.log_request_details("DELETE")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("<html><body><h1>DELETE Request Received!</h1></body></html>".encode('utf-8'))

    def log_request_details(self, method):
        """Helper method to log common request details."""
        self.log_message("Incoming Request: %s %s", method, self.path)
        self.log_message("Headers:")
        for header, value in self.headers.items():
            self.log_message("  %s: %s", header, value)

# --- Main Server Setup ---
def run_server():
    """
    Sets up and runs the HTTP server.
    """
    global w3_instance, reputation_contract, owner_eth_account

    # Define the SQLite database path and query for keys
    DB_FILE_PATH = '/var/lib/torrust/index/database/sqlite3.db'
    SQL_QUERY_KEYS = 'select tracker_key, username from torrust_user_authentication natural join torrust_user_profiles natural join torrust_users natural join torrust_tracker_keys;'

    # Load keys from database once when the server starts
    db_results = query_sqlite_db(DB_FILE_PATH, SQL_QUERY_KEYS)
    
    # Convert list of dicts to the tracker_key:username map
    keys_map = {u['tracker_key']: u['username'] for u in db_results} if db_results else {}
    
    print(f"Loaded {len(keys_map)} user keys from database.")

    # Initialize Web3 and Contract (once at startup)
    w3_instance, reputation_contract, owner_eth_account = initialize_web3_contract(
        WEB3_PROVIDER_URL,
        REPUTATION_CONTRACT_ADDRESS,
        REPUTATION_CONTRACT_ABI,
        OWNER_PRIVATE_KEY
    )

    # Initialize shared data container that will be passed to handler instances
    shared_server_data = {
        'torrents': {},  # Per-torrent, per-key stats in memory
        'keys': keys_map,  # The pre-loaded user keys map
        'user_stats': {k: {'uploaded': 0, 'downloaded': 0} for k in keys_map.keys()} # Initialize user_stats
    }

    Handler = RequestLoggerHandler
    # Pass shared_server_data to the custom server class
    with CustomThreadingTCPServer(("", PORT), Handler, shared_data=shared_server_data) as httpd:
        print(f"Serving HTTP requests on port {PORT}...")
        print(f"To test, open your browser and go to http://127.0.0.1:{PORT}/")
        print("Press Ctrl+C to stop the server.")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down the server...")
            httpd.shutdown()
            print("Server stopped.")


if __name__ == "__main__":
    run_server()

