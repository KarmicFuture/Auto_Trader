import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "network-mapper"))

import network_map  # noqa: E402


class NetworkMapTests(unittest.TestCase):
    def test_normalize_and_lookup_vendor(self):
        self.assertEqual(network_map.normalize_mac("44-d9-e7-00-10-01"), "44:D9:E7:00:10:01")
        self.assertEqual(network_map.lookup_vendor("44:D9:E7:00:10:01"), "Ubiquiti")
        self.assertEqual(network_map.lookup_vendor("not-a-mac"), "")

    def test_classify_gateway_printer_camera_and_school(self):
        gateway = network_map.classify_device(
            network_map.Device(ip="192.168.1.1", is_gateway=True, open_ports=[53, 80])
        )
        self.assertEqual(gateway.kind, "router")
        self.assertEqual(gateway.zone, "core")

        printer = network_map.classify_device(
            network_map.Device(ip="192.168.1.40", hostname="office-laserjet", open_ports=[9100])
        )
        self.assertEqual(printer.kind, "printer")
        self.assertEqual(printer.zone, "shared")

        camera = network_map.classify_device(
            network_map.Device(ip="192.168.1.50", hostname="front-door-cam", open_ports=[554])
        )
        self.assertEqual(camera.kind, "camera")
        self.assertEqual(camera.zone, "iot")

        school = network_map.classify_device(
            network_map.Device(ip="192.168.1.20", hostname="school-chromebook", vendor="Google")
        )
        self.assertEqual(school.kind, "chromebook")
        self.assertEqual(school.zone, "school")

    def test_demo_report_covers_the_three_practices(self):
        result = network_map.demo_result()
        zones = {d.zone for d in result.devices}
        self.assertTrue({"core", "work", "school", "consulting", "iot", "guest", "shared"} <= zones)
        self.assertTrue(any(r.zone == "consulting" for r in result.recommendations))
        self.assertTrue(any("VLAN" in r.detail or "VLAN" in r.title for r in result.recommendations))

        with tempfile.TemporaryDirectory() as tmp:
            paths = network_map.write_outputs(result, Path(tmp))
            html = paths["html"].read_text()
            markdown = paths["markdown"].read_text()
            data = json.loads(paths["json"].read_text())

            self.assertIn("Household network map", html)
            self.assertIn("Recommended design", html)
            self.assertIn("consulting-thinkpad", html)
            self.assertIn("school-chromebook", html)
            self.assertIn('data-panel="plan"', html)
            self.assertIn("VLAN 30 · Consulting", html)
            self.assertIn("flowchart TB", markdown)
            self.assertEqual(data["mode"], "demo")
            self.assertEqual(data["counts"]["devices"], len(result.devices))

    def test_iter_targets_and_ipv6_rejected(self):
        hosts = network_map.iter_targets("192.168.1.0/30")
        self.assertIn("192.168.1.1", hosts)
        self.assertIn("192.168.1.2", hosts)
        with self.assertRaises(ValueError):
            network_map.iter_targets("fe80::/64")

    def test_scan_refuses_huge_ranges_without_force(self):
        with self.assertRaises(SystemExit):
            network_map.scan_network(
                cidr="10.0.0.0/16",
                timeout=0.05,
                workers=4,
                ports=False,
                force=False,
            )

    def test_cli_demo_writes_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = network_map.main(["--demo", "--out", tmp])
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "network-map.html").is_file())
            self.assertTrue((Path(tmp) / "network-map.md").is_file())
            self.assertTrue((Path(tmp) / "network-map.json").is_file())


if __name__ == "__main__":
    unittest.main()
