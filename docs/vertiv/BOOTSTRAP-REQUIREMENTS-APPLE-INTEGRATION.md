# Vertiv Integrated Infrastructure Platform

## Bootstrap Conversation and Product Requirements

**Status:** Conversation starter — not a frozen specification
**Audience:** Vertiv product, engineering, services, and GTM
**North star:** Inventory is discovered in minutes. Configuration and monitoring follow automatically.
**Analogy we are copying:** How Apple integrates hardware, identity, location, and operations into one closed loop.

---

## 0. How to use this document

This is a **bootstrap conversation**, not a PRD that pretends the answers already exist.

Read it in this order, and stop to argue at each gate:

1. **The problem we actually have** (Vertiv already owns the pieces; they do not close the loop).
2. **What Apple does that we do not** (intended state vs live state vs telemetry, with the rack as the unit of integration).
3. **What DCP, Sunbird, nlyte, and DSView each already do well** (steal the right capabilities, not the product names).
4. **The three-move product** we must ship: **Find → Configure → Watch**.
5. **The questions we still have to answer as Vertiv** (the conversation).

If a section does not change what we would build in the next 90 days, skip it. The only non-negotiable is this:

> A rack, a PDU, a UPS, a cooling unit, a KVM, a serial console, and a server should go from **unknown** to **inventoried, configured, and monitored** without a spreadsheet, a Visio file, or a two-week professional-services engagement.

---

## 1. The conversation we are having

Vertiv is not starting from zero. We already sell the physical stack Apple-class operators put in a hall:

- Power: UPS, busway, floor PDU, rack PDU (Geist / Server Technology lineage)
- Thermal: CRAC/CRAH, rear-door, liquid, iCOM
- IT access: Avocent KVM, ACS serial, service processors, rack managers
- Monitoring remnants: Environet, DSView Solution
- Discontinued system-of-record software: Avocent Data Center Planner (DCP), Trellis, SiteScan

Sunbird and nlyte won the **system of record** and **change workflow** layers after we walked away from DCP and Trellis. DSView still wins **out-of-band control**. Nobody in our portfolio currently wins the thing hyperscalers actually do:

**They do not “do DCIM.” They integrate.**

Apple’s public pattern (Private Cloud Compute hardware integrity, plus how Apple-owned data centers are staffed and instrumented) is the model:

1. The rack is assembled and **recorded as intended state** before it ever reaches a live hall.
2. At deploy time, the hall **re-verifies** that intended state against live hardware identity (BMC / service processor / serial / cryptographic identity).
3. The asset database is updated **immediately** on every physical change. It is not a quarterly audit artifact.
4. Facilities telemetry (electrical + mechanical) and IT identity live in the same operational picture.
5. Drift is an incident. Unknown inventory is a defect.

That is the product Vertiv should build. Not another dashboard. An **integration fabric** that uses the hardware we already manufacture as the discovery and control plane.

---

## 2. North star: the Apple integration pattern, restated as Vertiv product language

Apple does not treat inventory as a reporting problem. Inventory is a **manufacturing and deployment contract**.

### 2.1 The three records that must always agree

| Record | What it is | Apple analogue | Vertiv analogue we must own |
| --- | --- | --- | --- |
| **Intended state** | As-designed / as-built of the rack and hall | Integration-center rack layout written to the data center asset database; manufacturing asset database of components and identities | Rack BOM + port map + power chain + cooling adjacency, created at factory, integration center, or first power-on |
| **Live state** | What is actually plugged in and answering | BMC query: components and cryptographic identities match both databases; physical location sample-audited | Auto-discovery via Redfish / IPMI / SNMP / serial / LLDP / PDU outlet mapping / KVM-attached targets |
| **Operational telemetry** | What it is doing right now | Tamper, health, and facility telemetry; MQTT / SCADA / analytics stack for electrical and mechanical | PDU kW, UPS, cooling, sensors, SP health, session audit, alarms |

The product fails unless **intended ≠ live** is a first-class event, not a consulting project.

### 2.2 The unit of integration is the rack (then the row, then the hall)

Hyperscalers do not onboard “a server.” They onboard a **rack as a finished good**:

- Known U-positions and serials
- Known PDU outlet-to-PSU mapping
- Known network and serial/KVM paths
- Known power budget vs measured load
- Known firmware baseline
- Known monitoring endpoints and credentials vault

Vertiv already ships most of those physical parts. The software gap is that we never issued the rack a **birth certificate** and never ran a **power-on reconciliation**.

### 2.3 The one-sentence product

> **Find everything that is there, prove it matches what was supposed to be there, configure it to a standard, and start watching it — in one pass, on Vertiv hardware, without a DCIM priesthood.**

---

## 3. Capability review: what each product actually does

These are working notes for the conversation, not vendor marketing. Capabilities are grouped the way the product must work: **inventory, configure, monitor**, plus the supporting layers (plan, change, control).

### 3.1 Avocent / Vertiv Data Center Planner (DCP)

**What it was:** Visual system of record for the physical hall. Discontinued. Formerly MergePoint Infrastructure Explorer.

**What it did well (steal this):**

- Floor and rack **digital twin**: drag-and-drop placement of floor-mount and rack-mount assets from a device library (space, power, heat, weight, network ports).
- **Capacity search** across plans: find a home by remaining U, power, cooling, weight, or user-defined properties.
- **End-to-end connection visualization** (power and network).
- **Project / what-if** planning and rack timeline: see when a rack will run out of space, power, or ports.
- **Global view** of multiple sites on a map with capacity colorization.
- **System of record** intent: location, space, rack power, connectivity, network — one place Facilities and IT could share.
- Integration hooks to **DSView**, **Rack Power Manager**, and **Liebert SiteScan**: events, reboot/shutdown, power status, average power — i.e. DCP was already trying to be the map, with DSView as the hands.

**What it did not do (do not rebuild the failure mode):**

- Inventory was largely **modeled by people**, not discovered. The device library accelerated drawing; it did not replace walking the row.
- Auto-discovery of live identity (serial, BMC, MAC, outlet) was not the product.
- Auto-configuration of PDUs, SPs, KVMs, trap destinations, and firmware baselines was not the product.
- Monitoring was delegated to other products; DCP showed a picture, it did not run the hall.
- Heavy client, rack licensing, certificate-stitched integrations — high friction, low “rack arrives, it exists.”

**Bootstrap takeaway:** DCP is the **intended-state canvas** we still need. It is not the discovery engine and not the monitor. Rebuilding DCP as a Visio replacement is a trap.

### 3.2 Sunbird (dcTrack + Power IQ)

**What it is:** Current market reference for “DCIM that people actually use.” Two products that are meant to work together: **dcTrack** (operations / assets / capacity) and **Power IQ** (monitoring / PDU management).

**What it does well (steal this):**

- **Asset inventory that behaves like a spreadsheet people will keep current:** filterable asset lists, custom fields, 2D/3D rack elevations, barcode/QR audit, parts and spares down to DIMMs and SFPs.
- **Huge vendor model library** (tens of thousands of templates): U height, weight, power, ports pre-populated so provisioning is not a drawing exercise.
- **Capacity as a search problem:** remaining space, power, cooling, network ports, power connectors; reserve capacity; find stranded capacity.
- **Auto Power Budget:** per make/model instance power budget from *measured* load, not nameplate — this is the closest commercial analogue to hyperscale power planning.
- **Power IQ autodiscovery of rack PDUs**, vendor-neutral SNMP, bulk config and firmware for Raritan / Server Technology / CPI (names, SNMP, traps, passwords, IPs).
- **Single-line power diagrams**, panel schedules, busway, UPS, actual vs budget at every hop.
- **Connectivity:** visual trace, cable length, port-level power and data.
- **Zero-config dashboards** and 3D capacity overlays — time-to-value is the sales motion.
- **REST APIs** used in the wild to *script* PDU onboarding (discover default IP → SSH configure → register in dcTrack and Power IQ). That customer pattern is the product we should ship natively.

**What it still is not (the gap Apple would not accept):**

- Discovery of **IT identity** is incomplete; VMware sync exists, but the physical rack is still largely a human-maintained model reconciled after the fact.
- Auto-configuration of the **full Vertiv stack** (KVM, serial, SP, UPS, cooling) is not a Sunbird job.
- Intended-state-from-factory is not native. The birth certificate is missing.
- Out-of-band **control** (KVM, serial, virtual media, SP) is not Sunbird.
- The two-product split (dcTrack vs Power IQ) still requires mapping work. Apple would not tolerate two sources of truth for the same PDU.

**Bootstrap takeaway:** Sunbird is the **usability and power-ops bar**. If our inventory UX is worse than dcTrack, or our PDU bulk-config is worse than Power IQ, we will lose the room. We should not try to out-feature Sunbird’s BI widgets. We should **collapse Find → Configure → Watch onto Vertiv metal**.

### 3.3 nlyte

**What it is:** Enterprise DCIM as a **lifecycle and workflow** system, not just a map. Asset Optimizer, Energy Optimizer, Discovery / Asset Explorer, ITSM connectors, Operational AI.

**What it does well (steal this):**

- **Dock-to-decom lifecycle:** receiving, staging, install, operate, refresh, retire — inventory starts at the loading dock, not after the server is in the rack.
- **Workflow engine** for moves/adds/changes: approvals, work orders, audit trail, no-code process. This is how regulated enterprises keep the CMDB honest.
- **Discovery as reconciliation:** agentless network scan (Nlyte Discovery / Asset Explorer) walks subnets, then **reconciles live vs system of record**. Unknown and zombie assets are a feature, not an accident.
- **ITSM/CMDB synchronization** (ServiceNow, BMC, Cherwell) — nlyte assumes it is not the only system of record; it keeps the enterprise record true.
- **Power, environmental, energy** monitoring and capacity modeling, plus visualization of racks, power paths, thermal.
- **Hybrid / edge / colo** posture: desktops to halls to IoT, tenant and remote-site operations.
- **Conversational ops (Nlyte Intelligence):** ask the estate questions instead of hunting dashboards.

**What it still is not:**

- Deep **out-of-band control** of Vertiv access hardware.
- Native **factory / integration-center birth certificate** for a Vertiv rack.
- Automatic **device configuration** (PDU trap dest, SP accounts, KVM paths, firmware gold image) as a one-click outcome of discovery.
- Time-to-value is historically a **program**, not a power-on. Apple would not wait for a workflow design workshop to know what is in the rack.

**Bootstrap takeaway:** nlyte is the **governance and reconciliation bar**. We need dock-to-decom and live-vs-intended matching. We do not need to become ServiceNow. We do need a reconciliation engine so discovery never silently overwrites intended state.

### 3.4 DSView (legacy 4.5 and current DSView Solution / former ADX)

**What it is:** Vertiv’s remaining **IT control plane**. Secure, centralized, out-of-band access and automation for KVM, serial, service processors, virtual machines, and Geist rack PDUs. Hub-and-spoke (4.5) evolved to MP1000 / RM1048P / HTML5 / REST (DSView Solution).

**What it does well (this is our unfair advantage):**

- **Discovery of physically connected devices** — KVM-attached targets, serial-attached consoles, Redfish service processors, ACS, Geist PDUs. This is live inventory, not a drawing.
- **Topology sync, name push/pull, merge targets** (classic DSView): the access layer already has a notion of “what is on this port.”
- **Service processor management** (IPMI / iLO / DRAC historically; Redfish on the current platform).
- **Hands-on when the OS is dead:** HTML5 KVM, serial, virtual media, session share, LED locator, firmware bulk update.
- **REST APIs** for device inventory and session launch — enough to hang a helpdesk or an orchestration loop on.
- **Alarms, audit, RBAC, AD/LDAP, 2FA**, zone granularity.
- **Same session plane for physical and virtual** (VMware, etc.).
- Guide-spec already requires: discover connected devices, manage Geist PDUs, Redfish SPs, ACS serial, IP KVM, firmware, REST.

**What it does not do (why DSView never became DCIM):**

- It knows **access topology**, not **hall topology**. It will tell you what is on port 12. It will not tell you that the rack is in row D, U19, on panel 4H-7, in the cold aisle of Hall 2, with 4.1 kW budgeted and 2.7 kW measured.
- It does not own **space / weight / cooling / power-chain capacity**.
- It does not own **dock-to-decom** or work orders.
- Auto-discovery is **appliance-adjacent**, not hall-wide subnet + BMC + PDU + LLDP fusion.
- Configuration is **device-centric** (this PDU, this SP), not **rack-standard-centric** (apply gold image to every new rack of type X).
- The DCP integration that used to put DSView “on the map” is gone with DCP.
- Environet watches facilities; DSView controls IT; they do not share a birth certificate.

**Bootstrap takeaway:** DSView is the **live-state and control plane**. It is the query path Apple would use instead of sending a human to the cage. It must become the discovery sensor for the new platform, not a separate console operators log into after DCIM is “done.”

---

## 4. Side-by-side: who wins which move today

| Move | DCP (legacy) | Sunbird | nlyte | DSView | Apple pattern | Vertiv target |
| --- | --- | --- | --- | --- | --- | --- |
| **Find** — what is in the hall, fast | Modelled, library-assisted | Human + barcode + PDU autodiscover + VM sync | Dock receive + network discovery + reconcile | Connected-port / SP / PDU discovery | Factory record + BMC identity match at deploy | **Fusion discovery:** birth certificate + DSView/Redfish/SNMP/serial/LLDP + dock scan |
| **Prove** — intended vs live | Weak | Manual audit | Strong reconciliation vs CMDB | Names/topology sync only | Hard requirement | First-class drift object |
| **Configure** — gold image the box | No | PDU bulk config (Power IQ) | Workflow, not device config | Firmware, some PDU/SP | Image to production release before certs | **Policy pack:** identity, SNMP/Redfish, traps, names, firmware, outlets, sessions |
| **Watch** — telemetry and alert | Via SiteScan / RPM / DSView | Power IQ excellence | Energy + environment | SP health, session, PDU | Facilities + tamper + health | One bus: power, thermal, IT health, access |
| **Plan** — where can this go | Excellent | Excellent | Excellent | No | Capacity is a placement API | Keep DCP/Sunbird-class search |
| **Change** — MAC with audit | Projects | Work orders | Best in class | Session audit only | Immediate DB update | nlyte-class, lighter |
| **Control** — fix it without a flight | Via DSView hop | PDU outlet | Limited | **Best in class** | BMC + process | DSView remains the hands |
| **Time to first inventory** | Days–weeks | Days if disciplined | Weeks (program) | Minutes for connected gear | Minutes at rack power-on | **Minutes per rack** |

The empty cells in **Vertiv target** are the product.

---

## 5. The product we are specifying

Working name for the conversation: **Vertiv Integrate** (platform). Three verbs only.

```
                    ┌─────────────────────────────────────────┐
                    │           INTENDED STATE                │
                    │  Factory / integration / design BOM     │
                    │  Rack birth certificate (FSD analogue)  │
                    └──────────────────┬──────────────────────┘
                                       │ reconcile
   FIND  ──────────────────────────────▼
                    ┌─────────────────────────────────────────┐
                    │             LIVE STATE                  │
                    │  DSView + Redfish + SNMP + serial +     │
                    │  PDU outlets + LLDP + dock barcode      │
                    └──────────────────┬──────────────────────┘
                                       │ apply policy pack
   CONFIGURE  ─────────────────────────▼
                    ┌─────────────────────────────────────────┐
                    │          STANDARD CONFIG                │
                    │  Names, creds, firmware, traps,         │
                    │  outlets, KVM/serial paths, sensors     │
                    └──────────────────┬──────────────────────┘
                                       │ subscribe
   WATCH  ─────────────────────────────▼
                    ┌─────────────────────────────────────────┐
                    │         OPERATIONAL TELEMETRY           │
                    │  Power, thermal, health, tamper,        │
                    │  sessions, drift, capacity              │
                    └─────────────────────────────────────────┘
```

### 5.1 Design constraints (non-negotiable)

1. **Inventory is the first screen, not a module.** If Find takes more than one sitting, the product is wrong.
2. **No professional-services tax to get a rack on camera.** Services exist to handle exceptions, not to type serial numbers.
3. **Vertiv hardware is a first-class sensor.** A Geist PDU, ACS, IP KVM, RM1048P, Liebert unit, and Liebert/Vertiv UPS should announce themselves and their downstream.
4. **Vendor-neutral for the rest.** Sunbird and nlyte already proved customers will not rip Cisco, Dell, or APC to please the DCIM vendor.
5. **Intended state is write-once-from-source, not redrawn.** Factory, integration center, or customer design tool emits the birth certificate. The hall does not re-draw it.
6. **Configure is automatic and idempotent.** Re-running onboarding does not brick the rack.
7. **Monitor subscriptions are a consequence of inventory**, not a second project.
8. **DSView is a plane, not an app.** KVM/serial/SP are functions of an asset, not a destination.
9. **Environet-class facilities data and DSView-class IT data share an asset ID.**
10. **Unknown is louder than healthy.** A device answering on the network that is not in intended state is an alarm, not a nice-to-have report.

---

## 6. Requirements: Find (inventory)

The entire conversation hangs on this section. If Find is slow or dishonest, Configure and Watch are fiction.

### 6.1 Birth certificate (intended state)

**REQ-INV-001.** Every managed rack SHALL have a machine-readable **Rack Birth Certificate (RBC)** produced before or at first power-on.

Minimum RBC contents:

- Site, hall, row, rack ID, GPS/grid coordinate optional
- Frame model, serial, U height, weight rating, containment type
- Per-U expected occupant: manufacturer, model, serial (if known), role
- Power: upstream panel/circuit, PDU models/serials, outlet-to-device map, redundant path
- Access: KVM/serial/SP endpoints, expected MAC/BMC IDs
- Network: planned switch ports / interconnects (even if filled later)
- Thermal: caging, rear door, CDU ports if liquid
- Firmware gold-image pointers
- Schema version and checksum

**REQ-INV-002.** RBC SHALL be generable from any of: Vertiv factory / configure-to-order, customer integration center, Vertiv Modular Designer / BIM, or a first-seen discovery that is then **promoted** to intended state (explicit human confirm).

**REQ-INV-003.** RBC SHALL be immutable history: every revision is appended. Apple’s “change log for the entire history of a chassis” is the bar.

### 6.2 Fusion discovery (live state)

**REQ-INV-010.** The platform SHALL discover live inventory by fusing **all** of the following that are present, not requiring all of them:

| Sensor | What it proves |
| --- | --- |
| Avocent IP KVM / RM | Something with a video/USB identity is in this U-path |
| ACS / serial | Hostname, OS-less identity, network gear |
| Redfish / IPMI / iLO / iDRAC | Manufacturer, model, serial, MAC, health, location if set |
| Geist / Vertiv rack PDU | Outlet draw, sometimes hostname via LLDP/CDP; outlet map |
| SNMP (vendor-neutral) | UPS, PDU, cooling, sensors |
| Modbus / BACnet / MQTT | Facilities devices Environet already speaks |
| LLDP / CDP from ToR | MAC-to-port, which proves rack adjacency |
| Barcode / RFID / QR dock scan | Receiving event before the rack is live |
| Customer CMDB / nlyte / Sunbird API | External intended or live records to reconcile |

**REQ-INV-011.** Time-to-first-inventory for a powered Vertiv-standard rack (PDU + at least one discovery path) SHALL be **under 15 minutes**, unattended after network reachability.

**REQ-INV-012.** Time-to-hall-baseline (greenfield, Vertiv-heavy) SHALL be **hours, not weeks**: scan the management VRF, classify, propose RBC promotions, wait for human confirm only on conflicts.

**REQ-INV-013.** Discovery SHALL be agentless for infrastructure. No agent on compute unless the customer opts in.

### 6.3 Identity and location

**REQ-INV-020.** Every asset SHALL have a stable **AssetUID** that survives IP change, PDU move, and DSView re-add. Bind on (manufacturer, serial) first; fall back to (BMC MAC, service tag, KVM dongle ID, PDU serial+outlet).

**REQ-INV-021.** Physical location SHALL be a first-class attribute: site / hall / row / rack / U / position (front/rear). Location confidence: `factory` | `discovered` | `scanned` | `human` | `conflict`.

**REQ-INV-022.** The platform SHALL support Apple-style **deploy verification**: given RBC, query live BMC/SP/PDU and produce a pass/fail bill of materials. Failures block “in production” state.

**REQ-INV-023.** Subcomponents (PSU, DIMM, disk, NIC, SFP) SHOULD be inventoried when the SP exposes them. This is how you detect silent hardware swap.

### 6.4 Reconciliation (the nlyte move)

**REQ-INV-030.** Live findings SHALL never silently overwrite intended state. They create a **Drift** object: extra, missing, serial mismatch, location mismatch, firmware mismatch, unmapped outlet.

**REQ-INV-031.** Operator actions on Drift: accept (promote live → intended), restore (intended is truth, ticket to field), ignore with expiry, or merge.

**REQ-INV-032.** “Unknown on management network” SHALL be a default-on alarm class.

### 6.5 Inventory UX (the Sunbird / DCP move)

**REQ-INV-040.** First-run UX is a **hall list that fills itself**, not a blank floor plan. Drawing is optional enrichment.

**REQ-INV-041.** Spreadsheet-grade asset grid: sort, filter, bulk edit, export. If this is worse than Excel, people will leave.

**REQ-INV-042.** One-click rack elevation (2D required, 3D optional) with live power overlay when PDU is known.

**REQ-INV-043.** Search is capacity-aware: “find 4U + 2 kW + 2 copper + serial” across the estate (DCP Capacity Search / Sunbird reserve).

**REQ-INV-044.** Import from DCP exports, dcTrack, nlyte, CSV, and RBC JSON SHALL be supported so we can steal brownfield, not demand a reboot.

---

## 7. Requirements: Configure (automatic)

Discovery without configuration is a catalog. Apple images to a production release **before** the machine is trusted. We must do the infrastructure equivalent.

### 7.1 Policy packs

**REQ-CFG-001.** A **Policy Pack** is a versioned, idempotent desired config for a role: `vertiv-rack-standard-v3`, `edge-micro-v1`, `colo-tenant-pdu-v2`.

Typical pack contents:

- Naming convention (`{site}-{row}-{rack}-{role}`)
- NTP, DNS, syslog, SNMP v3, trap/inform destinations
- Redfish/IPMI accounts and certs (from vault, never in Git plaintext)
- Firmware baseline per SKU
- PDU outlet names bound to RBC U-map
- Sensor thresholds (inlet, door, humidity)
- DSView enrollment (zones, permissions, session policy)
- Environet / telemetry bus enrollment
- Door lock / cabinet policy if present

**REQ-CFG-002.** Onboarding a new asset SHALL be: classify → match pack → dry-run diff → apply → verify. Human click is allowed; human typing of 40 SNMP fields is not.

**REQ-CFG-003.** Apply SHALL be bulk (Sunbird Power IQ bar: firmware, passwords, trap dest, SNMP, IP, names across a fleet).

**REQ-CFG-004.** Apply SHALL be safe: pre-check reachability, take config backup, apply, post-check, auto-rollback on loss of management path.

### 7.2 Vertiv-owned devices (must be best in the world)

**REQ-CFG-010.** Geist / Vertiv rack PDU: autodiscover, set identity, outlet map from RBC, trap dest, firmware, and **start polling** without a second product.

**REQ-CFG-011.** Avocent ACS: port auto-discovery, pinout, baud if needed, probe strings, target names from RBC.

**REQ-CFG-012.** Avocent IP KVM / RM1048P / MP1000: target merge, session paths, virtual media policy, PoE port control where applicable.

**REQ-CFG-013.** Service processors: Redfish account, NTP, syslog, event subscription, firmware baseline.

**REQ-CFG-014.** Vertiv UPS, CRAC/CRAH, CDU, busway meters: protocol template (SNMP/Modbus/BACnet), point list, alarm mapping.

### 7.3 Enrollment is the configuration of monitoring

**REQ-CFG-020.** Successful configure SHALL **automatically create** the Watch subscriptions: pollers, trap receivers, threshold templates, DSView device record, capacity model entry.

**REQ-CFG-021.** There is no “now go set this up in Environet” step. If that sentence exists in a runbook, the requirement failed.

### 7.4 Secrets and identity

**REQ-CFG-030.** Credentials live in a vault. Policy Packs reference roles, not passwords.

**REQ-CFG-031.** Device unique certs / TPM / SP identity SHOULD be recorded on the AssetUID (Apple manufacturing-database analogue). Optional for v1; designed in.

---

## 8. Requirements: Watch (monitor)

Monitoring is not a product we sell on top. It is the steady state after Find + Configure.

### 8.1 One asset, many signals

**REQ-MON-001.** Telemetry is keyed by AssetUID. A PDU kW reading, an SP thermal, a KVM session, and a CRAC state are facets of assets in a topology, not rows in separate tools.

**REQ-MON-002.** Signal classes:

- Power: chain from utility-facing meter to outlet (Sunbird single-line bar)
- Thermal: inlet, aisle, liquid, CDU
- Health: SP sensors, PDU comms, cooling unit, UPS
- Access: DSView sessions, failed logins, virtual media
- Integrity: tamper, door, serial-mismatch drift
- Capacity: actual vs budget vs RBC

**REQ-MON-003.** Default thresholds come from the Policy Pack. Operators tune; they do not invent.

### 8.2 Control from the same object

**REQ-MON-010.** From any asset: launch KVM/serial (DSView), power-cycle outlet, graceful shutdown if supported, mark locator LED, acknowledge alarm. DCP’s old “open a DSView session from the map” is table stakes, except the map is now live.

**REQ-MON-011.** Power status and average power (legacy DCP + Rack Power Manager) SHALL be native, not a plug-in afterthought.

### 8.3 Facilities + IT on one bus

**REQ-MON-020.** Ingest Environet / SiteScan-like points and DSView events onto one timeline per rack.

**REQ-MON-021.** Open telemetry: SNMP, Modbus, BACnet, Redfish events, MQTT (this is how modern halls, including Apple-style facilities stacks, already move data). We adapt to the bus; we do not demand a forklift.

### 8.4 Capacity is monitored, not only planned

**REQ-MON-030.** Nameplate is a last resort. Budget comes from measured history per model instance (Sunbird Auto Power Budget analogue).

**REQ-MON-031.** Load-shift / loss-of-redundancy on dual-cord devices SHALL alarm.

---

## 9. Supporting requirements (plan, change, ecosystem)

These matter, but they are not the bootstrap. Ship them so Find → Configure → Watch is believed.

### 9.1 Plan (keep DCP / Sunbird)

- What-if placements against **live remaining** capacity, not last quarter’s spreadsheet.
- Power-chain headroom at every hop.
- Liquid / high-density constraints as first-class (CDU, manifold, rear door).

### 9.2 Change (keep nlyte, make it lighter)

- Work order optional, not mandatory for a PDU rename.
- Every apply, discover, and accept-drift writes an audit record (who, what, before, after).
- Immediate intended-state update on completed field work — Apple’s “database is updated immediately following changes.”

### 9.3 APIs and coexistence

We will not displace every Sunbird or nlyte estate on day one. We will sit under or beside them.

**REQ-ECO-001.** REST + events (webhooks/MQTT) for AssetUID CRUD, Drift, telemetry, session launch.

**REQ-ECO-002.** Bidirectional connectors: ServiceNow CMDB, dcTrack, nlyte, NetBox, customer asset DB.

**REQ-ECO-003.** DSView Solution remains the session implementation; the platform is the only place operators should *need* to look.

**REQ-ECO-004.** Export/import RBC JSON so factory, partners, and hyperscaler customers can generate intended state in *their* integrator, not only in our UI.

---

## 10. What “Apple integration” means as a Vertiv program (not a feature list)

If we are honest, Apple does not buy “DCIM.” They build a factory-to-hall contract. Vertiv’s version of that program:

| Apple move | Vertiv program move |
| --- | --- |
| Integration center records the rack into the asset DB | Configure-to-order and integration partners emit RBC as a shippable artifact with the rack |
| Deploy-time re-verify against BMC and manufacturing IDs | DSView/Redfish/PDU fusion vs RBC; fail closed |
| Manufacturing DB of component crypto identities | Record SP/BMC/NIC identities at factory or first boot; store on AssetUID |
| Immediate DB updates on moves | Drift + work complete → intended state, no nightly CSV |
| Physical location audits | Location confidence + sample audit workflow |
| Facilities MQTT / SCADA + IT identity | One AssetUID across Environet-class and DSView-class data |
| Image to production before trust | Policy Pack firmware + config before “monitored/production” flag |
| Tamper and integrity as ops signals | Door, serial mismatch, unexpected SP, extra MAC as integrity alarms |

**We are not claiming we will sell this to Apple.** We are claiming we will **productize the method** so the next Apple-like operator (or Apple-like internal standard at a colo, bank, or national cloud) can buy it from Vertiv instead of staffing 40 people to glue Geist, Liebert, and Avocent to a homegrown CMDB.

---

## 11. Explicit non-goals (for the first conversation)

Say no out loud so the document stays small:

- We will not rebuild Trellis as a modular enterprise suite that takes 18 months to land.
- We will not compete with ServiceNow on ITSM.
- We will not require 3D digital twins before inventory is true.
- We will not make operators draw the hall before they can see the hall.
- We will not ship another standalone “PDU manager,” “KVM manager,” and “thermal manager” that do not share AssetUID.
- We will not assume every customer rips Sunbird or nlyte. Coexistence is a requirement, conquest is a strategy.

---

## 12. Conversation guide — questions Vertiv still has to answer

This section is the meeting. Do not skip it for a prettier architecture slide.

### 12.1 Strategy

1. Are we willing to **re-enter DCIM**, or are we building an **integration fabric** that makes Environet + DSView + factory data look like one product and lets Sunbird/nlyte sit on top?
2. Is the first buyer **hyperscale / national cloud**, **colo**, or **enterprise**? Find → Configure → Watch is the same; the RBC source (factory vs customer integrator) is not.
3. Do we treat **Geist PDU + Avocent RM** as the thin-edge sensor that makes every rack “Vertiv-visible” even when compute is Dell/HPE/SuperMicro?
4. What is the relationship to **Environet**? Absorb, sibling, or sunset-into?

### 12.2 Inventory truth

5. Who is allowed to write intended state: factory, partner, customer DC ops, or all three with signed provenance?
6. For brownfield with no RBC, is **first discovery + human promote** acceptable, or do we require a barcode walk?
7. Do we store subcomponent serials in v1 (Apple-hard) or only chassis+PDU?

### 12.3 Configure blast radius

8. Will Legal/Security accept Vertiv software that **sets SP passwords and firmware** at fleet scale? (This is the Power IQ lesson: it is the feature, and it is the risk.)
9. Gold image source of truth: Vertiv-published SKU baselines, customer-owned, or both?
10. How do we handle **partial packs** (PDU yes, SP no) without leaving a rack “half monitored”?

### 12.4 Platform shape

11. Control plane: extend **DSView Solution (MP1000 / REST)** as the kernel, or a new service that *calls* DSView and Environet?
12. Tenant model: colo landlord vs tenant vs enterprise edge at 10,000 sites?
13. Offline / dark-site: Apple-like air gap. Does configure/watch work with a rack manager as the local brain?

### 12.5 Honest capability bets

14. Can we beat Sunbird on **PDU bulk config** in 12 months? If no, partner or acquire the UX, keep the hardware hook.
15. Can we beat nlyte on **ServiceNow reconcile**? If no, ship a clean CMDB connector and win on power-on time.
16. Can we beat everyone on **minutes-to-inventory for a Vertiv rack**? If we cannot, we should not start.

---

## 13. Suggested conversation outcome (decision record)

Fill this in live. The document has done its job if these are no longer blank.

| Decision | Options | We chose | Why |
| --- | --- | --- | --- |
| Product type | Full DCIM vs integration fabric vs DSView+Environet glue | | |
| First persona | Factory/integration vs hall ops vs remote NOC | | |
| First SKU hook | Rack PDU, Rack Manager, or full Vertiv rack | | |
| Intended-state source | Factory RBC vs discover-and-promote | | |
| Coexistence | Replace Sunbird/nlyte vs sit underneath | | |
| Kernel | DSView Solution vs new platform vs Environet | | |
| v1 success metric | Minutes-to-inventory? Packs applied? Drift mean-time-to-detect? | | |

---

## 14. v1 acceptance — the demo that ends the argument

Do not accept a roadmap that cannot be demoed as follows.

**Setup:** One Vertiv rack, unknown to the software, on a management switch. RBC file on a USB stick or factory QR. Policy Pack `demo-v1` already in the system.

**Script:**

1. Scan the QR / import RBC. Intended state appears: empty live, full intended.
2. Power the rack. Within 15 minutes, live state fills: PDU serial, outlet map, SP serials, KVM/serial targets.
3. Drift shows one intentional mismatch (wrong serial in U12). Operator accepts or flags.
4. One click: apply Policy Pack. PDU names, trap dest, SP NTP/syslog, DSView enrollment, firmware check.
5. Watch starts without a second wizard: kW per outlet, inlet temp, SP health, session launch from the rack elevation.
6. Pull the network cable on the SP. Integrity/health alarm on the **same** asset the kW is on.
7. Launch KVM from that asset. Fix. Alarm clears.

If that demo needs two products, a services engineer, and a spreadsheet, we are still selling the 2015 stack.

---

## 15. Capability-to-requirement trace (for the skeptics)

| We looked at | We keep | We reject as the core |
| --- | --- | --- |
| **DCP** | Device library, capacity search, floor/rack intended map, DSView-from-the-map | Manual-first inventory, discontinued architecture |
| **Sunbird** | Usable asset grid, model library, PDU autodiscover, bulk config, actual-vs-budget power, fast dashboards | Split brain (dcTrack vs Power IQ), weak factory identity, no OOB control |
| **nlyte** | Dock-to-decom, live-vs-record reconcile, CMDB, workflow/audit | Slow time-to-value, weak device configure, weak OOB |
| **DSView** | Connected discovery, SP/KVM/serial/PDU control, REST, firmware, audit | Hall capacity, lifecycle, facilities bus, rack birth certificate |
| **Apple** | Three-record loop, rack as finished good, verify-at-deploy, immediate updates, integrity as ops | Building a private stack only Apple can staff |

---

## 16. Closing — the sentence to put on the whiteboard

**Sunbird shows the hall. nlyte governs the hall. DCP drew the hall. DSView touches the hall.**

**Apple integrates the hall: it already knows what should be there, confirms what is there, configures it to standard, and watches it as one object.**

Vertiv is the only company that can put the sensor, the actuator, the power, and the cooling in that loop **because we manufacture them.** The requirement is not a bigger DCIM. The requirement is to **stop asking customers to integrate us.**

---

## Appendix A — Glossary

| Term | Meaning in this document |
| --- | --- |
| **RBC** | Rack Birth Certificate — machine-readable intended state |
| **AssetUID** | Stable identity for an asset across IP, tool, and move |
| **Drift** | First-class object for intended vs live disagreement |
| **Policy Pack** | Versioned desired config + monitor subscription |
| **Fusion discovery** | Combining multiple sensors into one live state |
| **Find → Configure → Watch** | The only three product verbs |
| **DCP** | Avocent / Vertiv Data Center Planner (discontinued visual SoR) |
| **DSView** | Avocent management software / current DSView Solution (OOB control) |

## Appendix B — Sources used for capability notes

Public product material only; treat as conversation input, not a competitive-intelligence dump.

- Vertiv Data Center Planner product page and Installer/User Guide (visualization, device library, DSView / Rack Power Manager / SiteScan integration)
- Avocent DCP brochure (system of record, what-if, connection visualization)
- Sunbird dcTrack / Power IQ datasheets and PDU application notes (asset model library, Auto Power Budget, PDU autodiscover and bulk config)
- nlyte DCIM / Asset Optimizer / Discovery public pages (lifecycle, workflow, reconcile, ITSM)
- Vertiv DSView Solution / ADX MP1000 guide spec and API notes (connected discovery, Redfish, REST, Geist PDU, firmware)
- Apple Security Research, Private Cloud Compute — Hardware Integrity (integration-center record, deploy re-verify, BMC identity match, change logs, location audit)
- Public Apple data center engineering postings (facilities telemetry stack: MQTT, SCADA, electrical+mechanical cohesion)

---

*End of bootstrap. Next meeting: fill Section 13, then cut v1 to whatever is required to run Section 14 without embarrassment.*
