import http.server
import socketserver
import threading
import sys
from urllib.parse import urlparse, parse_qs
import sqlite3
database = {}
keys = {}
torrents = {}
user_stats = {}

# Define the port to listen on.
# Note: To open port 80, you might need administrator/root privileges
# (e.g., run with `sudo python your_script_name.py` on Linux/macOS,
# or ensure proper permissions on Windows).
PORT = 8091

# --- Custom Request Handler ---
# This class extends SimpleHTTPRequestHandler to customize its behavior.
# It only handles GET requests and logs their details.


class RequestLoggerHandler(http.server.SimpleHTTPRequestHandler):
    """
    A custom HTTP request handler that specifically logs GET requests,
    including details parsed from /announce paths and query parameters,
    to standard output (stdout).
    """

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
        except:
            pass

    def do_GET(self):
        """Handle GET requests."""
        self.log_request_details("GET")

        # Check for X-Original-URI header for mirrored requests
        original_uri = self.headers.get('X-Original-URI')

        if original_uri:
            parsed_original_url = urlparse(original_uri)
            original_path_segments = parsed_original_url.path.split('/')

            # Extract dynamic announce ID (X) from original path
            original_announce_id = None
            if len(original_path_segments) >= 3 and original_path_segments[1] == 'announce':
                self.log_message(
                    "--- Original Request Details (from X-Original-URI) ---")
                original_announce_id = original_path_segments[2]
                auth_key = original_announce_id
                if auth_key is None or auth_key == "":
                    pass
                else:
                    self.log_message(
                        "Original Announce ID (X): %s", original_announce_id)

                    # Parse query parameters from original URI
                    params = parse_qs(parsed_original_url.query)
                    self.log_announce_params(params)
                    # Define variables with parsed parameter values
                    info_hash_val = params.get('info_hash', [None])[0]
                    peer_id_val = params.get('peer_id', [None])[0]
                    port_val = params.get('port', [None])[0]
                    uploaded_val = params.get('uploaded', [None])[0]
                    if uploaded_val is None:
                        uploaded_val = 0
                    else:
                        uploaded_val = int(uploaded_val)
                    downloaded_val = params.get('downloaded', [None])[0]
                    if downloaded_val is None:
                        downloaded_val = 0
                    else:
                        downloaded_val = int(downloaded_val)
                    left_val = params.get('left', [None])[0]
                    corrupt_val = params.get('corrupt', [None])[0]
                    key_val = params.get('key', [None])[0]
                    numwant_val = params.get('numwant', [None])[0]
                    compact_val = params.get('compact', [None])[0]
                    no_peer_id_val = params.get('no_peer_id', [None])[0]
                    supportcrypto_val = params.get('supportcrypto', [None])[0]
                    redundant_val = params.get('redundant', [None])[0]
                    ip_val = params.get('ip', [None])[0]
                    ipv6_val = params.get('ipv6', [None])[0]
                    event_val = params.get('event', [None])[0]

                    if torrents.get(info_hash_val) is None:
                        torrents[info_hash_val] = {}
                    else:
                        if torrents[info_hash_val].get(auth_key) is None:
                            torrents[info_hash_val][auth_key] = {}

                        if torrents[info_hash_val][auth_key].get('uploaded') is None or torrents[info_hash_val][auth_key]['uploaded'] < uploaded_val:
                            torrents[info_hash_val][auth_key]['uploaded'] = uploaded_val
                            user_stats[auth_key]['uploaded'] += uploaded_val

                        if torrents[info_hash_val][auth_key].get('downloaded') is None or torrents[info_hash_val][auth_key]['downloaded'] < downloaded_val:

                            torrents[info_hash_val][auth_key]['downloaded'] = int(
                                downloaded_val)
                            user_stats[auth_key]['downloaded'] += int(
                                downloaded_val)

                    if auth_key is not None:
                        username = keys.get(auth_key)
                        if username is not None:
                            self.log_message("-----------------------")
                            self.log_message(
                                f"Auth Key '{auth_key}' is belonging to user: {username}")
                            self.log_message(
                                f"  User {username} reporting Uploaded: {uploaded_val}, Downloaded: {downloaded_val} for torrent {info_hash_val}")

                            self.log_message(
                                f"  User {username} reporting Uploaded: {user_stats[auth_key]['uploaded']}, Downloaded: {user_stats[auth_key]['downloaded']} overall")
                            self.log_message("-----------------------")
                        else:
                            self.log_message(f"-----------------------")
                            self.log_message(
                                f"Warning: Auth Key '{auth_key}' does not belong to a known user.")
                            self.log_message("-----------------------")
                    else:
                        self.log_message(
                            "Warning: Auth Key (Passkey) not provided in request.")

        # Send a simple 200 OK response back to the client
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response_message = f"<html><body><h1>Request Received!</h1><p>Method: GET</p><p>Path: {self.path}</p></body></html>"
        self.wfile.write(response_message.encode('utf-8'))

    def log_announce_params(self, params):
        """Helper function to log common announce parameters."""
        self.log_message("  Info Hash: %s", params.get('info_hash', [None])[0])
        self.log_message("  Peer ID: %s", params.get('peer_id', [None])[0])
        self.log_message("  Port: %s", params.get('port', [None])[0])
        self.log_message("  Uploaded: %s", params.get('uploaded', [None])[0])
        self.log_message("  Downloaded: %s",
                         params.get('downloaded', [None])[0])
        self.log_message("  Left: %s", params.get('left', [None])[0])
        self.log_message("  Corrupt: %s", params.get('corrupt', [None])[0])
        self.log_message("  Key (Passkey): %s", params.get('key', [None])[0])
        self.log_message("  Num Want: %s", params.get('numwant', [None])[0])
        self.log_message("  Compact: %s", params.get('compact', [None])[0])
        self.log_message("  No Peer ID: %s",
                         params.get('no_peer_id', [None])[0])
        self.log_message("  Support Crypto: %s",
                         params.get('supportcrypto', [None])[0])
        self.log_message("  Redundant: %s", params.get('redundant', [None])[0])
        self.log_message("  Client IP: %s", params.get('ip', [None])[0])
        self.log_message("  Client IPv6: %s", params.get('ipv6', [None])[0])
        self.log_message("  Event: %s", params.get('event', [None])[0])

    def log_request_details(self, method):
        """Helper method to log common request details."""
        self.log_message("Incoming Request: %s %s", method, self.path)
        self.log_message("Headers:")
        for header, value in self.headers.items():
            self.log_message("  %s: %s", header, value)


def query_sqlite_db(db_path, query):
    """
    Connects to a SQLite database, executes a query, and returns the results
    as a list of dictionaries, where each dictionary represents a row
    with column names as keys.

    Args:
        db_path (str): The path to the SQLite database file.
        query (str): The SQL query string to execute.

    Returns:
        list[dict]: A list of dictionaries, each representing a row from the query result.
                    Returns an empty list if no results or on error.
    """
    conn = None  # Initialize conn to None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(query)

        # Get column names from cursor description
        column_names = [description[0] for description in cursor.description]

        rows = cursor.fetchall()

        # Parse results into a list of dictionaries
        result_dicts = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = row[i]
            result_dicts.append(row_dict)

        return result_dicts

    except sqlite3.Error as e:
        sys.stderr.write(f"SQLite error: {e}\n")
        return []
    except FileNotFoundError:
        sys.stderr.write(f"Error: Database file not found at {db_path}\n")
        return []
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred: {e}\n")
        return []
    finally:
        if conn:
            conn.close()

# --- Main Server Setup ---


def run_server():
    """
    Sets up and runs the HTTP server.
    """
    DB_FILE = "/var/lib/torrust/index/database/sqlite3.db"
    SQL_QUERY = 'select * from torrust_user_authentication natural join torrust_user_profiles natural join torrust_users natural join torrust_tracker_keys;'

    # Call the function to execute the query and get results as dictionaries
    database = query_sqlite_db(DB_FILE, SQL_QUERY)
    # {'user_id': 2, 'password_hash': '$argon2id$v=19$m=19456,t=2,p=1$fUqOhgf8SzU/lu+24p/8RA$Ua/5gEp57KWK5RpQtTvZmxnmndMV3viNv/7iRdTubxk', 'username': 'fake_fx', 'email': 'fake@fx.com', 'email_verified': 0, 'bio': None, 'avatar': None, 'date_registered': '2025-06-12 16:16:37', 'administrator': 0, 'date_imported': None, 'tracker_key_id': 2, 'tracker_key': 'Zo1AbKSIX0wCdU6LB683ktTXNeNk1i9Q', 'date_expiry': 1757002614}

    for u in database:
        key = u['tracker_key']
        keys[key] = {}
        keys[key]['username'] = u['username']
        user_stats[key] = {'uploaded': 0, 'downloaded': 0}

    if database:
        print("--- Parsed User Data ---")
        for user_dict in database:
            print(user_dict)
    else:
        print("No user data found or an error occurred.")

    Handler = RequestLoggerHandler
    with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
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
