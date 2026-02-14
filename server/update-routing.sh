#!/bin/bash
set -e

JSON=/opt/vpn/routing.json
CONF=/opt/vpn/nginx-routing-header.conf
URL=https://raw.githubusercontent.com/mkaminskiy/shadowrocket/main/KaminskiyVPN.v2raytun.routing.json

VERBOSE=false
if [ "$1" = "-v" ] || [ "$1" = "--verbose" ]; then
    VERBOSE=true
fi

log() {
    if $VERBOSE; then
        echo "$@"
    fi
}

# Download fresh JSON
log "Downloading JSON from $URL..."
curl -sf "$URL" -o "${JSON}.tmp"
log "Downloaded $(wc -c < "${JSON}.tmp") bytes"

# Skip if unchanged
if cmp -s "${JSON}.tmp" "$JSON" 2>/dev/null; then
    rm "${JSON}.tmp"
    log "JSON unchanged, skipping"
    exit 0
fi

mv "${JSON}.tmp" "$JSON"
log "JSON updated"

# Minify JSON and encode to base64
B64=$(python3 -c "import sys,json; json.dump(json.load(open('$JSON')),sys.stdout,ensure_ascii=False)" | base64 -w0)
LEN=${#B64}
CHUNK=3500
log "Base64 length: $LEN chars, splitting into chunks of $CHUNK"

i=0
n=0
vars=""
sets=""
while [ $i -lt $LEN ]; do
    n=$((i / CHUNK + 1))
    chunk=${B64:$i:$CHUNK}
    sets="${sets}set \$r${n} \"${chunk}\";\n"
    vars="${vars}\$r${n}"
    i=$((i + CHUNK))
done
log "Generated $n chunks"

printf "${sets}set \$routing \"${vars}\";\nadd_header routing \$routing always;\n" > "$CONF"
log "Written nginx config to $CONF"

# Reload nginx
nginx -t && nginx -s reload
log "Nginx reloaded"

if $VERBOSE; then
    RULES=$(python3 -c "import json; d=json.load(open('$JSON')); print(len(d['rules']))")
    echo "Done: $RULES rules, $n base64 chunks, $LEN chars total"
fi
