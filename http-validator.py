import requests

TIMEOUT = 7

def check_urls(input_file, output_file):
    with open(output_file, 'w') as www_file:
        with open(input_file, 'r') as urls_file:
            for url in urls_file:
                url = url.strip()
                print(f"Checking URL: {url}")
                
                try:
                    response = requests.head(url, timeout=TIMEOUT, verify=False)
                    response.raise_for_status()
                    
                    print(f"  Valid server found: {url}")
                    www_file.write(f"{url}\n")
                except requests.RequestException:
                    print(f"  No valid response from: {url} (or timed out)")

    print(f"Finished checking URLs. Valid HTTP servers have been written to {output_file}.")

if __name__ == "__main__":
    _input_file = "data/urls.txt"
    _output_file = "data/www.txt"
    check_urls(_input_file, _output_file)