ryu-manager publicsafety.py --observe-links --ofp-tcp-listen-port 6633 &
ryu-manager smarttraffic.py --observe-links --ofp-tcp-listen-port 6634 &
ryu-manager iot.py --observe-links --ofp-tcp-listen-port 6635 &
ryu-manager wifi.py --observe-links --ofp-tcp-listen-port 6636 &
ryu-manager connecting.py --observe-links --ofp-tcp-listen-port 6637 &