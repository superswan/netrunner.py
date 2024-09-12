import os
import shodan
import argparse
import configparser
import time
import xml.etree.ElementTree as ET

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']['ShodanAPIKey']

def setup_data_directory(scan_name):
    data_dir = os.path.join('data', scan_name)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def search_shodan(api, query, limit=None):
    try:
        results = []
        total_results = api.count(query)['total']
        print(f"Creating target list with {total_results} results")
        for i, result in enumerate(api.search_cursor(query), start=1):
            results.append(result)
            if i % 100 == 0 or i == total_results:
                percentage = (i / total_results) * 100
                print(f"Progress: {percentage:.2f}% ({i}/{total_results})")

            if limit and i >= limit:
                break
        
        if total_results % 100 != 0 and (not limit or total_results < limit):
            percentage = 100
            print(f"Progress: {percentage:.2f}% ({total_results}/{total_results})")
        
        return results
    except shodan.APIError as e:
        print(f'Error: {e}')
        return None

def save_targets(results, filepath):
    targets = [f"{result['ip_str']}:{result['port']}" for result in results if 'ip_str' in result and 'port' in result]
    with open(filepath, 'w') as file:
        for target in targets:
            file.write(f"{target}\n")
    print(f'Targets saved to {filepath}')

def get_all_ports(api, ip):
    try:
        host = api.host(ip)
        return [f"{ip}:{port}" for port in host.get('ports', [])]
    except shodan.APIError as e:
        print(f'Error looking up {ip}: {e}')
        return []

def parse_xml_template(template_path):
    tree = ET.parse(template_path)
    root = tree.getroot()

    scan_name = root.find('name').text
    shodan_query = root.find('shodan-query').text
    nuclei_command = root.find('nuclei-command').text
    parse_command = root.find('parse-command').text

    return scan_name, shodan_query, nuclei_command, parse_command

# Idk how to use XML so this is a hacky way to generate the command strings
def replace_placeholders(template_string, placeholders):
    for key, value in placeholders.items():
        template_string = template_string.replace(f"${{{key}}}", value)
    return template_string

def main():
    parser = argparse.ArgumentParser(description="Shodan data processing script")
    parser.add_argument('scan_name', help='Name of the scan template (without .xml extension)')
    parser.add_argument('--full', action='store_true', help='Perform full scan including all ports')
    parser.add_argument('--limit', type=int, help='Limit the number of results')
    
    args = parser.parse_args()

    template_path = os.path.join('scan-templates', f"{args.scan_name}.xml")
    
    if not os.path.exists(template_path):
        print(f"Error: Scan template '{args.scan_name}' not found in scan-templates directory.")
        return

    api = shodan.Shodan(load_config())
    scan_name, shodan_query, nuclei_command, parse_command = parse_xml_template(template_path)

    placeholders = {"name": scan_name}
    nuclei_command = replace_placeholders(nuclei_command, placeholders)
    parse_command = replace_placeholders(parse_command, placeholders)

    data_dir = setup_data_directory(scan_name)

    # Search Shodan
    print(f"Retrieving Shodan results for: {shodan_query}")
    results = search_shodan(api, shodan_query, limit=args.limit)
    if results:
        print(f"Found {len(results)} results for {shodan_query}")
        save_targets(results, os.path.join(data_dir, 'targets.txt'))

        if args.full:
            full_targets = set()
            for result in results:
                ip = result.get('ip_str')
                if ip:
                    full_targets.update(get_all_ports(api, ip))
                    time.sleep(1)  # Be nice to the API

            with open(os.path.join(data_dir, 'targets_full.txt'), 'w') as file:
                for target in full_targets:
                    file.write(f"{target}\n")
            print(f'Full targets saved to {os.path.join(data_dir, "targets_full.txt")}')
    
    # Print Nuclei and parse commands. Eventually will automatically run nuclei and parse results
    print(f"Nuclei Command: {nuclei_command}")
    print(f"Parse Command: {parse_command}")

if __name__ == "__main__":
    main()
