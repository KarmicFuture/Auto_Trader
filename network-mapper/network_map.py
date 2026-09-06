#!/usr/bin/env python3
"""Discover devices on the local LAN and build a home-network planning map.

Safe inventory only: ICMP echo, ARP table, reverse DNS, and optional
TCP connect checks on common identification ports. No exploits, no
credential tests, no vulnerability scanning.

Run this on a computer already connected to the network you own
(home Wi-Fi or Ethernet). The Cloud Agent VM is not your house LAN.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import ipaddress
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.request import pathname2url

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TIMEOUT = 0.35
DEFAULT_WORKERS = 64
MAX_HOSTS_WITHOUT_FORCE = 1024  # /22

# TCP connect-only. Used to guess device type, not to attack services.
IDENT_PORTS: dict[int, str] = {
    22: "ssh",
    53: "dns",
    80: "http",
    139: "netbios",
    443: "https",
    445: "smb",
    515: "lpd",
    548: "afp",
    554: "rtsp",
    631: "ipp",
    1883: "mqtt",
    3389: "rdp",
    5000: "http-alt",
    5357: "wsd",
    8006: "proxmox",
    8080: "http-proxy",
    8443: "https-alt",
    8831: "unifi",
    9100: "jetdirect",
    32400: "plex",
}

# Common OUIs. Keys are the first 3 octets, uppercase, no separators.
OUI_VENDORS: dict[str, str] = {
    "000C29": "VMware",
    "00155D": "Microsoft",
    "001A11": "Google",
    "001B11": "D-Link",
    "001B63": "Apple",
    "001D7E": "Cisco-Linksys",
    "001E13": "Cisco-Linksys",
    "001F3A": "Hon Hai / Foxconn",
    "00215A": "HP",
    "00226B": "Cisco-Linksys",
    "0024D7": "Intel",
    "0026B0": "Apple",
    "002719": "TP-Link",
    "0050F2": "Microsoft",
    "00E04C": "Realtek",
    "041552": "Apple",
    "04421A": "ASUS",
    "080027": "PCS Systemtechnik / VirtualBox",
    "086698": "Apple",
    "0C96BF": "Amazon",
    "105F06": "eero",
    "109397": "ARRIS",
    "14CC20": "TP-Link",
    "18B430": "Nest",
    "1C1BB5": "Intel",
    "205532": "Gionee / mobile",
    "246511": "AVM / FRITZ!",
    "28C2DD": "AzureWave / Intel",
    "2C08B4": "eero",
    "30AEA4": "Espressif",
    "34CE00": "Xiaomi",
    "38F9D3": "Apple",
    "3C5282": "Hewlett Packard",
    "3C5AB4": "Google",
    "40490F": "Hon Hai / Foxconn",
    "44D9E7": "Ubiquiti",
    "485D60": "AzureWave",
    "4C22F3": "Apple",
    "50C7BF": "TP-Link",
    "525400": "QEMU/KVM",
    "54AF97": "TP-Link",
    "5C5188": "Motorola",
    "60A4B7": "TP-Link",
    "68FF7B": "TP-Link",
    "70B3D5": "IEEE registered",
    "708BCD": "ASUS",
    "74DA38": "Edimax",
    "78D6DC": "Motorola",
    "7C2EBD": "Google",
    "80CC9C": "NETGEAR",
    "84A423": "Sagemcom",
    "88AD43": "Apple",
    "8C8590": "Apple",
    "90F652": "TP-Link",
    "94BFF6": "Apple",
    "98DED0": "TP-Link",
    "9C8E99": "Hewlett Packard",
    "A0F3C1": "TP-Link",
    "A44BD5": "Xiaomi",
    "A4C138": "Telink / IoT",
    "AC84C6": "TP-Link",
    "B0A737": "Roku",
    "B44BD2": "Apple",
    "B827EB": "Raspberry Pi",
    "B8C111": "Apple",
    "BC542F": "Intel",
    "C03F0E": "NETGEAR",
    "C46E1F": "TP-Link",
    "C83A35": "Tenda",
    "CC46D6": "Cisco",
    "D0C730": "Hewlett Packard",
    "D8EB46": "Google",
    "DCA632": "Raspberry Pi",
    "E0CB4E": "ASUS",
    "E45F01": "Raspberry Pi",
    "E8DE27": "TP-Link",
    "EC0BAE": "Hangzhou Hikvision",
    "F0B429": "Xiaomi",
    "F0F61C": "Apple",
    "F4F26D": "TP-Link",
    "F8A2D6": "Liteon / HP",
    "FC0199": "Murata / IoT",
    "FCF528": "Sony Interactive",
}

ZONE_META = {
    "core": {"label": "Core / gateway", "color": "#0f172a"},
    "work": {"label": "Work from home", "color": "#1d4ed8"},
    "school": {"label": "School", "color": "#047857"},
    "consulting": {"label": "Consulting", "color": "#6d28d9"},
    "personal": {"label": "Personal / family", "color": "#475569"},
    "iot": {"label": "IoT / cameras", "color": "#b45309"},
    "guest": {"label": "Guest", "color": "#be185d"},
    "shared": {"label": "Shared office", "color": "#0e7490"},
    "unknown": {"label": "Unclassified", "color": "#78716c"},
}


@dataclass
class Device:
    ip: str
    mac: str = ""
    hostname: str = ""
    vendor: str = ""
    kind: str = "host"
    zone: str = "unknown"
    is_gateway: bool = False
    is_self: bool = False
    open_ports: list[int] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    alive: bool = True

    def display_name(self) -> str:
        if self.hostname:
            return self.hostname
        if self.vendor:
            return f"{self.vendor} device"
        return self.ip


@dataclass
class NetworkContext:
    interface: str = ""
    cidr: str = ""
    self_ip: str = ""
    gateway: str = ""
    hostname: str = ""
    platform: str = platform.platform()
    ssid: str = ""
    dns: list[str] = field(default_factory=list)


@dataclass
class Recommendation:
    priority: str
    title: str
    detail: str
    zone: str = ""


@dataclass
class ScanResult:
    generated_at: str
    mode: str
    context: NetworkContext
    devices: list[Device]
    recommendations: list[Recommendation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0


def _run(cmd: list[str], timeout: float = 8.0) -> str:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout or ""


def normalize_mac(mac: str) -> str:
    hexes = re.findall(r"[0-9A-Fa-f]{2}", mac.replace("-", ":"))
    if len(hexes) < 6:
        return ""
    return ":".join(h.upper() for h in hexes[:6])


def lookup_vendor(mac: str) -> str:
    mac = normalize_mac(mac)
    if not mac:
        return ""
    prefix = mac.replace(":", "")[:6]
    if prefix in OUI_VENDORS:
        return OUI_VENDORS[prefix]
    for path in (
        Path("/usr/share/nmap/nmap-mac-prefixes"),
        Path("/usr/share/misc/nmap-mac-prefixes"),
        Path("/opt/homebrew/share/nmap/nmap-mac-prefixes"),
        Path("/usr/share/ieee-data/oui.txt"),
        Path("/usr/share/misc/oui.txt"),
    ):
        vendor = _vendor_from_file(path, prefix, mac)
        if vendor:
            return vendor
    return ""


def _vendor_from_file(path: Path, prefix: str, mac: str) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return ""
    if path.name.endswith("oui.txt"):
        dashed = "-".join(prefix[i : i + 2] for i in range(0, 6, 2))
        match = re.search(rf"^{re.escape(dashed)}\s+\(hex\)\s+(.+)$", text, re.I | re.M)
        return match.group(1).strip() if match else ""
    match = re.search(rf"^{re.escape(prefix)}\s+(.+)$", text, re.I | re.M)
    return match.group(1).strip() if match else ""


def _linux_context() -> NetworkContext:
    ctx = NetworkContext()
    route = _run(["ip", "-4", "route", "show", "default"])
    match = re.search(r"default via (\S+) dev (\S+)", route)
    if match:
        ctx.gateway, ctx.interface = match.group(1), match.group(2)
    addr = _run(["ip", "-4", "-o", "addr", "show"])
    for line in addr.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        iface, cidr = parts[1], parts[3]
        if iface == "lo" or "/" not in cidr:
            continue
        if ctx.interface and iface != ctx.interface:
            continue
        ctx.interface = iface
        ctx.cidr = cidr
        ctx.self_ip = cidr.split("/")[0]
        break
    resolv = Path("/etc/resolv.conf")
    if resolv.is_file():
        ctx.dns = [
            line.split()[1]
            for line in resolv.read_text(errors="ignore").splitlines()
            if line.startswith("nameserver")
        ]
    wireless = _run(["iwgetid", "-r"]) or _run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"])
    if wireless:
        for line in wireless.splitlines():
            if line.startswith("yes:"):
                ctx.ssid = line.split(":", 1)[1]
                break
        else:
            ctx.ssid = wireless.strip().splitlines()[0]
    return ctx


def _darwin_context() -> NetworkContext:
    ctx = NetworkContext()
    route = _run(["route", "-n", "get", "default"])
    gw = re.search(r"gateway: (\S+)", route)
    iface = re.search(r"interface: (\S+)", route)
    if gw:
        ctx.gateway = gw.group(1)
    if iface:
        ctx.interface = iface.group(1)
    ifconfig = _run(["ifconfig", ctx.interface or "-a"])
    inet = re.search(r"inet (\d+\.\d+\.\d+\.\d+) netmask (0x[0-9a-fA-F]+)", ifconfig)
    if inet:
        ctx.self_ip = inet.group(1)
        mask_int = int(inet.group(2), 16)
        prefix = bin(mask_int).count("1")
        ctx.cidr = f"{ctx.self_ip}/{prefix}"
    airport = _run(
        [
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
            "-I",
        ]
    )
    ssid = re.search(r"\sSSID: (.+)", airport)
    if ssid:
        ctx.ssid = ssid.group(1).strip()
    return ctx


def _windows_context() -> NetworkContext:
    ctx = NetworkContext()
    cfg = _run(["ipconfig", "/all"])
    current_iface = ""
    current_ip = ""
    for raw in cfg.splitlines():
        line = raw.rstrip()
        if line and not line.startswith(" ") and not line.startswith("\t"):
            current_iface = line.strip(" :")
            current_ip = ""
        ip_m = re.search(r"IPv4 Address[^:]*: ([\d.]+)", line)
        if ip_m:
            current_ip = ip_m.group(1)
            ctx.self_ip = current_ip
            ctx.interface = current_iface
        mask_m = re.search(r"Subnet Mask[^:]*: ([\d.]+)", line)
        if mask_m and current_ip:
            net = ipaddress.IPv4Network(f"{current_ip}/{mask_m.group(1)}", strict=False)
            ctx.cidr = str(net)
        gw_m = re.search(r"Default Gateway[^:]*: ([\d.]+)", line)
        if gw_m:
            ctx.gateway = gw_m.group(1)
        dns_m = re.search(r"DNS Servers[^:]*: ([\d.]+)", line)
        if dns_m:
            ctx.dns.append(dns_m.group(1))
    return ctx


def detect_context() -> NetworkContext:
    system = platform.system()
    if system == "Linux":
        ctx = _linux_context()
    elif system == "Darwin":
        ctx = _darwin_context()
    elif system == "Windows":
        ctx = _windows_context()
    else:
        ctx = NetworkContext()
    ctx.hostname = socket.gethostname()
    ctx.platform = platform.platform()
    if not ctx.cidr and ctx.self_ip:
        ctx.cidr = f"{ctx.self_ip}/24"
    return ctx


def _ping_command(ip: str, timeout: float) -> list[str]:
    system = platform.system()
    wait = max(1, int(round(timeout)))
    if system == "Windows":
        return ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
    if system == "Darwin":
        return ["ping", "-c", "1", "-W", str(int(timeout * 1000)), ip]
    return ["ping", "-c", "1", "-W", str(wait), ip]


def ping_host(ip: str, timeout: float) -> bool:
    cmd = _ping_command(ip, timeout)
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout + 1.5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def parse_arp_table() -> dict[str, str]:
    mapping: dict[str, str] = {}
    proc = Path("/proc/net/arp")
    if proc.is_file():
        for line in proc.read_text().splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4 and parts[2] != "0x0":
                mac = normalize_mac(parts[3])
                if mac and mac != "00:00:00:00:00:00":
                    mapping[parts[0]] = mac
        return mapping
    text = _run(["arp", "-an"]) or _run(["arp", "-a"])
    for line in text.splitlines():
        ip_m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", line) or re.search(
            r"(\d+\.\d+\.\d+\.\d+)", line
        )
        mac_m = re.search(r"((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})", line)
        if ip_m and mac_m:
            mapping[ip_m.group(1)] = normalize_mac(mac_m.group(1))
    return mapping


def reverse_dns(ip: str, timeout: float) -> str:
    socket.setdefaulttimeout(timeout)
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        return name.rstrip(".")
    except (socket.herror, socket.gaierror, socket.timeout, OSError, TimeoutError):
        return ""


def probe_ports(ip: str, ports: Iterable[int], timeout: float) -> list[int]:
    open_ports: list[int] = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            if sock.connect_ex((ip, port)) == 0:
                open_ports.append(port)
        except OSError:
            pass
        finally:
            sock.close()
    return open_ports


def classify_device(device: Device) -> Device:
    blob = " ".join(
        [
            device.hostname.lower(),
            device.vendor.lower(),
            device.ip,
            " ".join(IDENT_PORTS.get(p, "") for p in device.open_ports),
        ]
    )
    ports = set(device.open_ports)

    if device.is_gateway or (53 in ports and (80 in ports or 443 in ports)):
        device.kind = "router"
        device.zone = "core"
        if not device.notes:
            device.notes.append("Likely the LAN default gateway or another router/AP.")
        return device

    printer_hints = ("printer", "print", "hp", "canon", "epson", "brother", "xerox", "jetdirect", "ipp")
    if 9100 in ports or 631 in ports or 515 in ports or any(h in blob for h in printer_hints):
        device.kind = "printer"
        device.zone = "shared"
        device.notes.append("Shared printer — keep reachable from work and school, not from IoT.")
        return device

    camera_hints = (
        "camera",
        "ring",
        "wyze",
        "reolink",
        "amcrest",
        "hikvision",
        "rtsp",
        "nvr",
        "doorbell",
    )
    if 554 in ports or any(h in blob for h in camera_hints):
        device.kind = "camera"
        device.zone = "iot"
        device.notes.append("Camera/NVR belongs on an IoT VLAN with no path to work files.")
        return device

    if 32400 in ports or "plex" in blob or "roku" in blob or "tv" in blob:
        device.kind = "media"
        device.zone = "iot"
        return device

    if 1883 in ports or any(h in blob for h in ("esp32", "espressif", "tasmota", "iot", "plug", "nest")):
        device.kind = "iot"
        device.zone = "iot"
        return device

    if 3389 in ports or 445 in ports or 5357 in ports:
        device.kind = "windows-pc"
        device.zone = "work"
        device.notes.append("Windows host — default to the work zone until you tag it otherwise.")
        return device

    if any(h in blob for h in ("chromebook", "classroom", "school")):
        device.kind = "chromebook"
        device.zone = "school"
        return device

    if any(h in blob for h in ("ipad", "tablet")):
        device.kind = "tablet"
        device.zone = "school"
        device.notes.append("Tablet defaulted to school; retag if it is a personal or work iPad.")
        return device

    if any(h in blob for h in ("iphone", "android", "pixel", "galaxy")):
        device.kind = "phone"
        device.zone = "personal"
        return device

    if "apple" in blob or 548 in ports:
        device.kind = "apple-computer"
        device.zone = "work"
        device.notes.append("Apple computer defaulted to work from home. Retag if it is personal-only.")
        return device

    if 22 in ports and (8006 in ports or "proxmox" in blob or "nas" in blob or "synology" in blob):
        device.kind = "server"
        device.zone = "work"
        return device

    if 22 in ports:
        device.kind = "linux-host"
        device.zone = "work"
        return device

    if device.vendor:
        device.kind = "host"
        device.zone = "unknown"
        device.notes.append("Responded on the LAN but had no strong type signal — label it by hand.")
        return device

    device.kind = "host"
    device.zone = "unknown"
    return device


def suggest_recommendations(result: ScanResult) -> list[Recommendation]:
    devices = result.devices
    zones = {d.zone for d in devices}
    kinds = {d.kind for d in devices}
    unknown = [d for d in devices if d.zone == "unknown" and not d.is_self]
    iot = [d for d in devices if d.zone == "iot"]
    work = [d for d in devices if d.zone == "work"]
    school = [d for d in devices if d.zone == "school"]
    recs: list[Recommendation] = []

    recs.append(
        Recommendation(
            "now",
            "Split the house into purpose-built zones",
            "One flat LAN mixes homework, client files, and cameras. Create four SSIDs or VLANs: "
            "Work, School, Consulting, and IoT/Guest. Same internet, different trust levels.",
            "core",
        )
    )
    recs.append(
        Recommendation(
            "now",
            "Give consulting its own isolated network",
            "Use a dedicated SSID or VLAN with client isolation, its own DNS, and no file-share "
            "access to family PCs. Client data should never share a broadcast domain with kids' "
            "devices or smart plugs. Add a travel hotspot as a backup WAN for calls.",
            "consulting",
        )
    )
    recs.append(
        Recommendation(
            "now",
            "Pin work-from-home to wired Ethernet",
            "Reserve a gigabit (or 2.5G) jack at the desk for the work machine. Keep video calls "
            "off congested Wi-Fi, and turn on QoS / Wi-Fi calling priority for Zoom and Meet.",
            "work",
        )
    )
    recs.append(
        Recommendation(
            "next",
            "Put school devices on a filtered SSID",
            "Chromebooks and study tablets get their own SSID with Safe Search / DNS filtering "
            "and an evening schedule. They can reach the shared printer, not cameras or the "
            "consulting VLAN.",
            "school",
        )
    )

    if iot or "camera" in kinds or "media" in kinds:
        recs.append(
            Recommendation(
                "now",
                "Park IoT on a no-lateral-movement VLAN",
                f"{len(iot) or 'Several'} smart / camera / media device(s) showed up. Block IoT from "
                "initiating connections to Work, School, and Consulting. Allow internet plus a "
                "single path to a home assistant if you use one.",
                "iot",
            )
        )
    else:
        recs.append(
            Recommendation(
                "next",
                "Create an IoT VLAN before the next gadget lands",
                "Even if the scan did not label cameras yet, cheap Wi-Fi devices will appear. "
                "Having the SSID ready is cheaper than cleaning up a flat network later.",
                "iot",
            )
        )

    if unknown:
        recs.append(
            Recommendation(
                "now",
                f"Label {len(unknown)} unknown device(s)",
                "Unknown hosts are the usual surprise (old phones, a neighbor's IoT, a forgotten "
                "camera). Match them by MAC vendor, then reserve or block their DHCP lease.",
                "unknown",
            )
        )

    if not any(d.kind == "printer" for d in devices):
        recs.append(
            Recommendation(
                "later",
                "Place the shared printer on a 'shared office' VLAN",
                "Work and school both need print. IoT and guest should not. A small allow-list "
                "to TCP 631/9100 is enough.",
                "shared",
            )
        )

    consumer = any(
        v in (d.vendor + d.hostname).lower()
        for d in devices
        for v in ("eero", "orbi", "google", "tplink", "tp-link", "netgear", "verizon", "att", "xfinity")
    )
    if consumer or any(d.kind == "router" for d in devices):
        recs.append(
            Recommendation(
                "next",
                "Decide whether the current gateway can do VLANs",
                "Consumer mesh (eero, Orbi, ISP combo) often cannot isolate VLANs cleanly. If "
                "yours cannot, put the ISP box in bridge mode and add a UniFi / Firewalla / "
                "OPNsense / Peplink gateway. That one upgrade unlocks the rest of the plan.",
                "core",
            )
        )

    recs.append(
        Recommendation(
            "next",
            "Add a guest SSID with client isolation",
            "Visiting clients, tutors, and friends should hit Guest only. No LAN shares, no "
            "printer by default, no mDNS browsing of family devices.",
            "guest",
        )
    )
    recs.append(
        Recommendation(
            "next",
            "Give work and consulting a UPS and a backup path",
            "A small UPS on the ONT/modem, gateway, and desk switch survives brief outages. "
            "Keep a phone-hotspot or LTE router tested so a consulting call can fail over.",
            "work",
        )
    )
    recs.append(
        Recommendation(
            "later",
            "Write a one-page network standard for the house",
            "Document SSID names, VLAN IDs (10 work, 20 school, 30 consulting, 40 IoT, 50 guest), "
            "DNS, and who may add devices. That is what you will actually maintain six months from now.",
            "core",
        )
    )

    if work and school and "iot" in zones:
        recs.insert(
            1,
            Recommendation(
                "now",
                "The current LAN already mixes work, school, and IoT",
                "This scan classified devices into more than one trust zone on the same subnet. "
                "That is the core risk: a cheap plug or a homework laptop can see a work share. "
                "Segmentation is the first robustness upgrade, not more Wi-Fi range.",
                "core",
            ),
        )
    return recs


def demo_result() -> ScanResult:
    ctx = NetworkContext(
        interface="demo0",
        cidr="192.168.1.0/24",
        self_ip="192.168.1.42",
        gateway="192.168.1.1",
        hostname="planner-laptop",
        ssid="HouseNet",
        dns=["192.168.1.1"],
        platform="demo",
    )
    devices = [
        Device(
            ip="192.168.1.1",
            mac="44:D9:E7:00:10:01",
            hostname="house-gateway",
            vendor="Ubiquiti",
            kind="router",
            zone="core",
            is_gateway=True,
            open_ports=[53, 80, 443],
            notes=["Current all-in-one Wi-Fi router. Confirm VLAN capability."],
        ),
        Device(
            ip="192.168.1.10",
            mac="F0:F6:1C:10:20:30",
            hostname="wfh-macbook",
            vendor="Apple",
            kind="apple-computer",
            zone="work",
            open_ports=[22],
            notes=["Daily WFH laptop. Move to a wired work jack."],
        ),
        Device(
            ip="192.168.1.11",
            mac="3C:52:82:AA:BB:01",
            hostname="consulting-thinkpad",
            vendor="HP",
            kind="windows-pc",
            zone="consulting",
            open_ports=[22, 3389],
            notes=["Consulting workstation — isolate from family and school devices."],
        ),
        Device(
            ip="192.168.1.20",
            mac="7C:2E:BD:00:11:22",
            hostname="school-chromebook",
            vendor="Google",
            kind="chromebook",
            zone="school",
            notes=["Homework device. Needs filtered DNS, not client-file access."],
        ),
        Device(
            ip="192.168.1.21",
            mac="88:AD:43:44:55:66",
            hostname="study-ipad",
            vendor="Apple",
            kind="tablet",
            zone="school",
        ),
        Device(
            ip="192.168.1.30",
            mac="B4:4B:D2:77:88:99",
            hostname="family-iphone",
            vendor="Apple",
            kind="phone",
            zone="personal",
        ),
        Device(
            ip="192.168.1.40",
            mac="D0:C7:30:12:34:56",
            hostname="office-laserjet",
            vendor="HP",
            kind="printer",
            zone="shared",
            open_ports=[631, 9100],
        ),
        Device(
            ip="192.168.1.50",
            mac="EC:0B:AE:98:76:54",
            hostname="front-door-cam",
            vendor="Hangzhou Hikvision",
            kind="camera",
            zone="iot",
            open_ports=[80, 554],
        ),
        Device(
            ip="192.168.1.51",
            mac="B0:A7:37:11:22:33",
            hostname="living-room-roku",
            vendor="Roku",
            kind="media",
            zone="iot",
        ),
        Device(
            ip="192.168.1.60",
            mac="30:AE:A4:DE:AD:01",
            hostname="smart-plug-1",
            vendor="Espressif",
            kind="iot",
            zone="iot",
            open_ports=[80, 1883],
        ),
        Device(
            ip="192.168.1.70",
            mac="0C:96:BF:AB:CD:EF",
            hostname="guest-phone",
            vendor="Amazon",
            kind="phone",
            zone="guest",
            notes=["Should never have been on the main LAN."],
        ),
        Device(
            ip="192.168.1.42",
            mac="B8:27:EB:00:42:01",
            hostname="planner-laptop",
            vendor="Raspberry Pi",
            kind="linux-host",
            zone="work",
            is_self=True,
            notes=["Host that ran this planner (demo)."],
        ),
    ]
    result = ScanResult(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        mode="demo",
        context=ctx,
        devices=devices,
        warnings=[
            "Demo inventory — not this machine's live LAN. Re-run without --demo at home."
        ],
    )
    result.recommendations = suggest_recommendations(result)
    return result


def iter_targets(cidr: str) -> list[str]:
    network = ipaddress.ip_network(cidr, strict=False)
    if isinstance(network, ipaddress.IPv6Network):
        raise ValueError("IPv6 scan is not supported; pass an IPv4 CIDR.")
    hosts = [str(ip) for ip in network.hosts()]
    if network.prefixlen >= 31:
        hosts = [str(ip) for ip in network]
    return hosts


def scan_network(
    cidr: str | None,
    timeout: float,
    workers: int,
    ports: bool,
    force: bool,
) -> ScanResult:
    started = time.time()
    ctx = detect_context()
    warnings: list[str] = []
    if cidr:
        ctx.cidr = cidr
    if not ctx.cidr:
        raise SystemExit(
            "Could not detect a local IPv4 subnet. Pass one explicitly, e.g. --cidr 192.168.1.0/24"
        )

    targets = iter_targets(ctx.cidr)
    if len(targets) > MAX_HOSTS_WITHOUT_FORCE and not force:
        raise SystemExit(
            f"{ctx.cidr} has {len(targets)} addresses. Narrow the range or pass --force."
        )
    if not ctx.gateway:
        warnings.append("No default gateway detected; the map will not mark a router.")
    if platform.system() != "Windows" and hasattr(os, "geteuid") and os.geteuid() != 0:
        warnings.append(
            "Running without root. Ping/ARP still work for many home routers; "
            "some hosts may stay hidden until you re-run with sudo."
        )

    alive: set[str] = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(ping_host, ip, timeout): ip for ip in targets}
        for future in concurrent.futures.as_completed(future_map):
            ip = future_map[future]
            try:
                if future.result():
                    alive.add(ip)
            except Exception:
                continue

    if ctx.self_ip:
        alive.add(ctx.self_ip)
    if ctx.gateway:
        alive.add(ctx.gateway)

    arp = parse_arp_table()
    for ip, _mac in arp.items():
        try:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(ctx.cidr, strict=False):
                alive.add(ip)
        except ValueError:
            continue

    devices: list[Device] = []
    port_list = list(IDENT_PORTS) if ports else []

    def enrich(ip: str) -> Device:
        mac = arp.get(ip, "")
        device = Device(
            ip=ip,
            mac=mac,
            hostname=reverse_dns(ip, timeout),
            vendor=lookup_vendor(mac) if mac else "",
            is_gateway=bool(ctx.gateway and ip == ctx.gateway),
            is_self=bool(ctx.self_ip and ip == ctx.self_ip),
            open_ports=probe_ports(ip, port_list, timeout) if port_list else [],
        )
        if device.is_self and not device.hostname:
            device.hostname = ctx.hostname
        return classify_device(device)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(8, workers // 2)) as pool:
        devices = list(pool.map(enrich, sorted(alive, key=_ip_sort)))

    result = ScanResult(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        mode="live",
        context=ctx,
        devices=devices,
        warnings=warnings,
        elapsed_seconds=round(time.time() - started, 2),
    )
    result.recommendations = suggest_recommendations(result)
    return result


def _ip_sort(ip: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in ip.split("."))
    except ValueError:
        return (999, 0, 0, 0)


def result_to_dict(result: ScanResult) -> dict:
    return {
        "generated_at": result.generated_at,
        "mode": result.mode,
        "elapsed_seconds": result.elapsed_seconds,
        "context": asdict(result.context),
        "warnings": result.warnings,
        "devices": [asdict(d) for d in result.devices],
        "recommendations": [asdict(r) for r in result.recommendations],
        "counts": {
            "devices": len(result.devices),
            "by_zone": _count_by(result.devices, "zone"),
            "by_kind": _count_by(result.devices, "kind"),
        },
    }


def _count_by(devices: list[Device], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for device in devices:
        key = getattr(device, attr) or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def render_markdown(result: ScanResult) -> str:
    ctx = result.context
    lines = [
        "# Network map and household plan",
        "",
        f"Generated {result.generated_at} ({result.mode} scan).",
        "",
        "## Current LAN",
        "",
        f"- Interface: `{ctx.interface or 'unknown'}`",
        f"- This machine: `{ctx.self_ip or 'unknown'}` ({ctx.hostname or 'unnamed'})",
        f"- Subnet: `{ctx.cidr or 'unknown'}`",
        f"- Gateway: `{ctx.gateway or 'unknown'}`",
        f"- Wi-Fi SSID: `{ctx.ssid or 'n/a'}`",
        f"- DNS: {', '.join(ctx.dns) if ctx.dns else 'n/a'}",
        f"- Devices found: **{len(result.devices)}**",
        "",
    ]
    if result.warnings:
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {w}" for w in result.warnings)
        lines.append("")
    lines += ["## Inventory", "", "| Zone | Kind | Name | IP | MAC | Vendor | Ports |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for device in result.devices:
        ports = ",".join(str(p) for p in device.open_ports) or "—"
        lines.append(
            f"| {device.zone} | {device.kind} | {device.display_name()} | {device.ip} | "
            f"{device.mac or '—'} | {device.vendor or '—'} | {ports} |"
        )
    lines += ["", "## Recommended target", "", mermaid_target(), ""]
    lines += ["## Plan", ""]
    for rec in result.recommendations:
        lines += [f"### [{rec.priority}] {rec.title}", "", rec.detail, ""]
    return "\n".join(lines) + "\n"


def mermaid_target() -> str:
    return """```mermaid
flowchart TB
    internet[Internet / ISP] --> ont[ONT or modem in bridge mode]
    ont --> fw[Router or firewall with VLANs]
    fw --> work[VLAN 10 Work WFH]
    fw --> school[VLAN 20 School]
    fw --> consulting[VLAN 30 Consulting]
    fw --> iot[VLAN 40 IoT]
    fw --> guest[VLAN 50 Guest]
    fw --> shared[Shared printer allow-list]
    work --> desk[Wired desk jack + WFH SSID]
    consulting --> client[Isolated SSID + optional VPN]
    school --> kids[Filtered school SSID]
    iot --> cams[Cameras plugs TVs]
```"""


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def render_html(result: ScanResult) -> str:
    data = result_to_dict(result)
    payload = json.dumps(data, indent=2)
    ctx = result.context
    zone_pills = "".join(
        f'<span class="pill" style="background:{ZONE_META.get(zone, ZONE_META["unknown"])["color"]}">'
        f"{_esc(ZONE_META.get(zone, ZONE_META['unknown'])['label'])} · {count}</span>"
        for zone, count in _count_by(result.devices, "zone").items()
    )
    warning_html = ""
    if result.warnings:
        warning_html = "<ul class='warn'>" + "".join(f"<li>{_esc(w)}</li>" for w in result.warnings) + "</ul>"

    rows = []
    for device in result.devices:
        color = ZONE_META.get(device.zone, ZONE_META["unknown"])["color"]
        flags = []
        if device.is_gateway:
            flags.append("gateway")
        if device.is_self:
            flags.append("this machine")
        rows.append(
            "<tr>"
            f"<td><span class='dot' style='background:{color}'></span>{_esc(device.zone)}</td>"
            f"<td>{_esc(device.kind)}</td>"
            f"<td>{_esc(device.display_name())}<div class='muted'>{_esc(' · '.join(flags))}</div></td>"
            f"<td>{_esc(device.ip)}</td>"
            f"<td class='mono'>{_esc(device.mac or '—')}</td>"
            f"<td>{_esc(device.vendor or '—')}</td>"
            f"<td class='mono'>{_esc(', '.join(str(p) for p in device.open_ports) or '—')}</td>"
            f"<td>{_esc(' '.join(device.notes))}</td>"
            "</tr>"
        )

    rec_cards = []
    for rec in result.recommendations:
        rec_cards.append(
            f"<article class='card rec { _esc(rec.priority) }'>"
            f"<div class='priority'>{_esc(rec.priority)}</div>"
            f"<h3>{_esc(rec.title)}</h3>"
            f"<p>{_esc(rec.detail)}</p>"
            f"</article>"
        )

    columns = []
    order = ["core", "work", "school", "consulting", "shared", "personal", "iot", "guest", "unknown"]
    grouped: dict[str, list[Device]] = {z: [] for z in order}
    for device in result.devices:
        grouped.setdefault(device.zone, []).append(device)
    for zone in order:
        items = grouped.get(zone) or []
        if not items:
            continue
        meta = ZONE_META.get(zone, ZONE_META["unknown"])
        cards = []
        for device in items:
            cards.append(
                "<div class='node'>"
                f"<strong>{_esc(device.display_name())}</strong>"
                f"<span>{_esc(device.kind)} · {_esc(device.ip)}</span>"
                f"<span class='mono'>{_esc(device.mac or 'no MAC yet')}</span>"
                "</div>"
            )
        columns.append(
            f"<section class='zone' style='--zone:{meta['color']}'>"
            f"<header>{_esc(meta['label'])}</header>"
            f"{''.join(cards)}"
            "</section>"
        )

    target_zones = [
        ("10", "Work from home", "Wired desk + WFH SSID. Laptops, dock, work phone. Full LAN to printer only."),
        ("20", "School", "Chromebooks / study tablets. Filtered DNS, bedtime schedule, printer yes, shares no."),
        ("30", "Consulting", "Isolated SSID or VLAN. Client VPN, no family mDNS, no IoT, optional guest conference."),
        ("40", "IoT", "Cameras, plugs, TVs, speakers. Internet out, no east-west, no work or school."),
        ("50", "Guest", "Client isolation on. Visitors and tutors. No printer unless you opt in."),
    ]
    target_html = "".join(
        f"<section class='target'><h3>VLAN {vid} · {name}</h3><p>{desc}</p></section>"
        for vid, name, desc in target_zones
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Network map · {_esc(ctx.cidr or 'planner')}</title>
  <style>
    :root {{
      --bg: #f4f1ea;
      --ink: #1c1917;
      --muted: #57534e;
      --card: #fffdf8;
      --line: #d6d3d1;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font: 16px/1.45 "Iowan Old Style", "Palatino Linotype", Palatino, serif;
      color: var(--ink);
      background: radial-gradient(1200px 500px at 10% -10%, #e7e5e4, transparent), var(--bg);
    }}
    header.hero, main {{ max-width: 1180px; margin: 0 auto; padding: 0 20px; }}
    header.hero {{ padding-top: 36px; padding-bottom: 8px; }}
    h1 {{ font-size: 2.1rem; margin: 0 0 8px; letter-spacing: -0.03em; }}
    .lede {{ color: var(--muted); max-width: 42em; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px 16px; margin: 16px 0 8px; color: var(--muted); font-size: 0.92rem; }}
    .pills {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0 20px; }}
    .pill {{ color: #fff; border-radius: 999px; padding: 4px 10px; font-size: 0.8rem; font-family: ui-sans-serif, system-ui, sans-serif; }}
    nav.tabs {{ display: flex; gap: 6px; flex-wrap: wrap; margin: 18px 0; }}
    nav.tabs button {{
      font: 600 0.92rem/1 ui-sans-serif, system-ui, sans-serif;
      border: 1px solid var(--line);
      background: var(--card);
      padding: 8px 12px;
      border-radius: 10px;
      cursor: pointer;
    }}
    nav.tabs button[aria-selected="true"] {{ background: #1c1917; color: #fff; }}
    .panel {{ display: none; padding-bottom: 64px; }}
    .panel.active {{ display: block; }}
    .map {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }}
    .zone {{
      background: var(--card);
      border: 1px solid var(--line);
      border-top: 6px solid var(--zone);
      border-radius: 14px;
      padding: 10px;
      min-height: 120px;
    }}
    .zone header {{ font-family: ui-sans-serif, system-ui, sans-serif; font-weight: 700; margin-bottom: 8px; }}
    .node {{
      background: #fafaf9;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px;
      margin: 8px 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .node span {{ font-size: 0.82rem; color: var(--muted); font-family: ui-sans-serif, system-ui, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.8rem; }}
    .muted {{ color: var(--muted); font-size: 0.8rem; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--card); border-radius: 12px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.88rem; }}
    th {{ background: #1c1917; color: #fff; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px; }}
    .card h3 {{ margin: 6px 0 8px; font-size: 1.05rem; }}
    .priority {{
      display: inline-block;
      font-family: ui-sans-serif, system-ui, sans-serif;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 2px 8px;
      border-radius: 999px;
      background: #e7e5e4;
    }}
    .rec.now .priority {{ background: #9f1239; color: #fff; }}
    .rec.next .priority {{ background: #1d4ed8; color: #fff; }}
    .rec.later .priority {{ background: #57534e; color: #fff; }}
    .target {{ background: var(--card); border-left: 5px solid #1c1917; padding: 10px 14px; margin: 10px 0; }}
    .warn {{ background: #fff7ed; border: 1px solid #fdba74; border-radius: 12px; padding: 12px 16px; }}
    .internet {{
      text-align: center;
      font-family: ui-sans-serif, system-ui, sans-serif;
      font-weight: 700;
      margin: 8px 0 16px;
      padding: 10px;
      border: 1px dashed var(--line);
      border-radius: 12px;
      background: #fff;
    }}
    details.json {{ margin-top: 24px; }}
    pre {{ overflow: auto; background: #1c1917; color: #f5f5f4; padding: 12px; border-radius: 10px; }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Household network map</h1>
    <p class="lede">
      Inventory of what is on this LAN, plus a plan to separate work-from-home,
      school, and a consulting practice without giving every gadget the same trust.
    </p>
    <div class="meta">
      <span>{_esc(result.generated_at)} · {_esc(result.mode)}</span>
      <span>Subnet {_esc(ctx.cidr or 'unknown')}</span>
      <span>Gateway {_esc(ctx.gateway or 'unknown')}</span>
      <span>SSID {_esc(ctx.ssid or 'n/a')}</span>
      <span>{len(result.devices)} device(s)</span>
    </div>
    <div class="pills">{zone_pills}</div>
    {warning_html}
    <nav class="tabs" role="tablist">
      <button type="button" role="tab" aria-selected="true" data-panel="current">Current map</button>
      <button type="button" role="tab" data-panel="target">Recommended design</button>
      <button type="button" role="tab" data-panel="inventory">Inventory</button>
      <button type="button" role="tab" data-panel="plan">Plan</button>
    </nav>
  </header>
  <main>
    <section id="current" class="panel active">
      <div class="internet">Internet → ISP modem/ONT → {_esc(ctx.gateway or 'gateway')} → this subnet</div>
      <div class="map">{''.join(columns)}</div>
    </section>
    <section id="target" class="panel">
      <p class="lede">Target architecture: one firewall, five zones, shared printer by allow-list only.</p>
      {target_html}
    </section>
    <section id="inventory" class="panel">
      <table>
        <thead><tr><th>Zone</th><th>Kind</th><th>Name</th><th>IP</th><th>MAC</th><th>Vendor</th><th>Ports</th><th>Notes</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
    <section id="plan" class="panel">
      <div class="cards">{''.join(rec_cards)}</div>
      <details class="json"><summary>Raw scan JSON</summary><pre>{_esc(payload)}</pre></details>
    </section>
  </main>
  <script>
    document.querySelectorAll("nav.tabs button").forEach((btn) => {{
      btn.addEventListener("click", () => {{
        document.querySelectorAll("nav.tabs button").forEach((b) => b.setAttribute("aria-selected", "false"));
        document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
        btn.setAttribute("aria-selected", "true");
        document.getElementById(btn.dataset.panel).classList.add("active");
      }});
    }});
  </script>
</body>
</html>
"""


def write_outputs(result: ScanResult, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "html": out_dir / "network-map.html",
        "markdown": out_dir / "network-map.md",
        "json": out_dir / "network-map.json",
    }
    paths["html"].write_text(render_html(result), encoding="utf-8")
    paths["markdown"].write_text(render_markdown(result), encoding="utf-8")
    paths["json"].write_text(json.dumps(result_to_dict(result), indent=2) + "\n", encoding="utf-8")
    return paths


def open_report(path: Path) -> None:
    uri = pathname2url(str(path.resolve()))
    url = f"file://{uri}"
    system = platform.system()
    if system == "Darwin":
        _run(["open", str(path)])
    elif system == "Windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        _run(["xdg-open", str(path)])
    if not sys.stdout.isatty():
        print(url)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discover LAN devices and write a WFH / school / consulting network plan."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Build a sample mixed-use household map without scanning.",
    )
    parser.add_argument("--cidr", help="IPv4 subnet to scan, e.g. 192.168.1.0/24")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Per-host timeout seconds")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Concurrent ping workers")
    parser.add_argument("--no-ports", action="store_true", help="Skip TCP identification probes")
    parser.add_argument("--force", action="store_true", help="Allow scanning more than 1024 addresses")
    parser.add_argument(
        "--out",
        default=str(SCRIPT_DIR / "output"),
        help="Directory for HTML, Markdown, and JSON reports",
    )
    parser.add_argument("--open", action="store_true", dest="open_html", help="Open the HTML map")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.demo:
        result = demo_result()
    else:
        result = scan_network(
            cidr=args.cidr,
            timeout=args.timeout,
            workers=args.workers,
            ports=not args.no_ports,
            force=args.force,
        )
    paths = write_outputs(result, Path(args.out))
    print(f"Mode:     {result.mode}")
    print(f"Subnet:   {result.context.cidr}")
    print(f"Gateway:  {result.context.gateway or 'unknown'}")
    print(f"Devices:  {len(result.devices)}")
    print(f"HTML:     {paths['html']}")
    print(f"Markdown: {paths['markdown']}")
    print(f"JSON:     {paths['json']}")
    if args.open_html:
        open_report(paths["html"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
