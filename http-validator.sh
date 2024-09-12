#!/bin/bash

> www.txt

TIMEOUT=10

while IFS= read -r url; do
    echo "Checking URL: $url"
    
    if curl -k --head --silent --fail --max-time $TIMEOUT "$url" > /dev/null; then
        echo "  Valid server found: $url"
        echo "$url" >> www.txt
    else
        echo "  No valid response from: $url (or timed out)"
    fi
done < urls.txt

echo "Finished checking URLs. Valid HTTP servers have been written to www.txt."

