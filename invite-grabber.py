import requests
import itertools
import time
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from colorama import Fore, Style, init

init(autoreset=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

chars = "abcdefghijklmnopqrstuvwxyz0123456789"
delay = 1
num_threads = 10
save_file = "last_code.txt"
output_file = "invites_valides.txt"
proxy_file = "proxies.txt"
progress_lock = Lock()
file_lock = Lock()
check_count = 0  # Pour pause auto

# === Bienvenue ===
def welcome():
    print(f"""
{Fore.MAGENTA}╔══════════════════════════════╗
║  Discord Invite BruteForcer  ║
╚══════════════════════════════╝
      By Cybershadow, MIT License®
""")
    if not os.path.exists(proxy_file):
        print(f"{Fore.RED}[ERREUR] Le fichier proxies.txt est manquant.")
        exit()

    if not os.path.exists(save_file):
        with open(save_file, "w") as f:
            f.write("")

    if not os.path.exists(output_file):
        open(output_file, "w").close()

    with open(proxy_file, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    print(f"{Fore.GREEN}[+] {len(proxies)} proxies chargés")
    last_code = load_last_code()
    if last_code:
        print(f"{Fore.YELLOW}[+] Reprise depuis : {last_code}")
    else:
        print(f"{Fore.BLUE}[+] Démarrage depuis le début.")
    return proxies

def get_proxy(proxies):
    proxy = random.choice(proxies)
    return {"http": proxy, "https": proxy}

def save_progress(code):
    with progress_lock:
        with open(save_file, "w") as f:
            f.write(code)

def load_last_code():
    with open(save_file, "r") as f:
        return f.read().strip()

def code_generator(chars):
    last = load_last_code()
    start = False if last else True

    for length in range(1, 9):
        for combo in itertools.product(chars, repeat=length):
            code = ''.join(combo)
            if not start:
                if code == last:
                    start = True
                continue
            yield code

def check_code(code, proxies):
    global check_count
    proxy = get_proxy(proxies)
    url = f"https://discord.com/api/v9/invites/{code}?with_counts=true"

    try:
        r = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        if r.status_code == 200:
            data = r.json()
            name = data['guild']['name']
            print(f"{Fore.GREEN}[VALIDE] {code} => {name}")
            with file_lock:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(f"{code} => {name}\n")
        elif r.status_code == 404:
            print(f"{Fore.RED}[INVALIDE] {code}")
        elif r.status_code == 429:
            print(f"{Fore.YELLOW}[RATE LIMIT] {code} | IP bannie temporairement")
        else:
            print(f"{Fore.RED}[ERREUR {r.status_code}] {code}")
    except Exception as e:
        print(f"{Fore.MAGENTA}[PROXY FAIL] {proxy['http']} | {e}")
    save_progress(code)

    # Incrémenter le compteur et pause toutes les 5s
    with progress_lock:
        check_count += 1
        if check_count % 5 == 0:
            print(f"{Fore.CYAN}[PAUSE] Attente 3s...")
            time.sleep(3)

    time.sleep(delay)

# === Lancement ===
def main():
    proxies = welcome()
    gen = code_generator(chars)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(check_code, code, proxies): code for code in gen}
        try:
            for future in as_completed(futures):
                future.result()
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}[STOP] Arrêt manuel.")
            executor.shutdown(wait=False)

if __name__ == "__main__":
    main()
