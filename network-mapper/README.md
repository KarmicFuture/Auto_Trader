# Network mapper

Scan the LAN you are on, write a visual map, and get a concrete plan for a house that has to do **work from home**, **school**, and **consulting** on the same internet connection.

The script only inventories *your* network: ICMP ping, the ARP table, reverse DNS, and optional TCP connect checks on common identification ports. It does not guess passwords, scan for vulnerabilities, or try exploits.

Run it on a laptop or desktop that is already joined to the home Wi-Fi or Ethernet. A cloud VM is not your house.

## Quick start

```bash
# Preview the planner with a sample mixed-use household (no scan)
python3 network-mapper/network_map.py --demo --open

# Live scan of the current IPv4 subnet
python3 network-mapper/network_map.py --open

# Or name the subnet yourself
python3 network-mapper/network_map.py --cidr 192.168.1.0/24 --open
```

No extra Python packages. On Linux, `sudo` can fill in more MAC addresses. On Windows and macOS the built-in `ping` / `arp` tools are enough.

Reports land in `network-mapper/output/` unless you pass `--out`:

| File | What it is |
| --- | --- |
| `network-map.html` | Interactive map, inventory, and the zone plan |
| `network-map.md` | Same content for notes or a ticket |
| `network-map.json` | Machine-readable inventory |

## What “robust” means here

A flat home LAN treats a work laptop, a homework Chromebook, a client workstation, and a cheap camera as equals. The report pushes you toward one firewall and five zones:

| VLAN | Zone | Who lives there |
| --- | --- | --- |
| 10 | Work from home | Your daily job laptop, dock, wired desk jack |
| 20 | School | Chromebooks and study tablets, filtered DNS |
| 30 | Consulting | Isolated SSID, client VPN, no family file shares |
| 40 | IoT | Cameras, plugs, TVs — internet only, no lateral movement |
| 50 | Guest | Visitors and tutors, client isolation on |

The shared printer is an allow-list, not a reason to flatten the network.

## Useful flags

```
--demo          Sample household, no packets
--cidr CIDR     IPv4 range (required if auto-detect fails)
--no-ports      Skip TCP identification probes
--timeout 0.35  Seconds per ping / connect
--workers 64    Concurrent pings
--force         Allow ranges larger than /22
--out DIR       Report directory
--open          Open the HTML map
```

Subnets bigger than 1024 addresses are refused unless you pass `--force`, so a mistaken `/16` does not sweep the building.

## Reading the map

1. **Current map** — devices grouped by guessed zone (work, school, consulting, IoT, …).
2. **Recommended design** — the target VLAN layout.
3. **Inventory** — IP, MAC, vendor, open identification ports, notes.
4. **Plan** — now / next / later steps based on what showed up.

Guesses come from hostname, MAC vendor, and a short port list (SSH, HTTP, SMB, RDP, IPP, RTSP, and similar). Retag anything that looks wrong; unknown hosts are usually the ones worth chasing.

## Tests

```bash
python3 -m unittest tests.test_network_map
```
