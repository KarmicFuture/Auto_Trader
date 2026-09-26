# How we should promote Vertiv

## Executive pitch — talk track

**Audience:** Vertiv ELT, GTM, product, and services leaders
**Time:** 12 minutes + discussion
**Ask:** Stop promoting Vertiv as a catalog of power, cooling, and racks. Promote Vertiv as the company that **integrates the hall** — inventory in minutes, then automatic configure and monitor — the way Apple integrates a rack.
**Companion:** [Bootstrap requirements](BOOTSTRAP-REQUIREMENTS-APPLE-INTEGRATION.md)

How to use this: say the **Talk** blocks out loud. Use **Do not say** as a self-check. The appendix is for Q&A, not the pitch.

---

## 0. The opening (45 seconds)

**Talk:**

We sell the physical stack that every serious data center actually runs on: power, cooling, racks, PDUs, KVM, serial, service processors. That is not the problem.

The problem is how we **promote** it. We still sound like a manufacturer with a software sidebar. Customers hear Geist, Liebert, Avocent, Environet, DSView — five brands, five consoles, a services SOW to glue them together.

Apple does not do that. Apple does not “do DCIM.” They integrate. A rack leaves the integration center with a known bill of materials. At deploy, they verify live hardware against that record. Then they configure it to a standard and watch it as one object. Unknown inventory is a defect. Drift is an incident.

We already manufacture the sensors and the actuators in that loop. We walked away from the software that tied it together — DCP, Trellis, SiteScan. Sunbird and nlyte took the system of record. We kept DSView, which can touch a device but cannot describe the hall.

The promotion shift is one sentence:

> **Vertiv does not ask you to integrate us. We arrive already integrated.**

That is how we should talk about Vertiv from now on. Everything else is a catalog.

---

## 1. Why this is an executive issue, not a product issue

**Talk:**

This is not a request to rebuild Trellis. Trellis was a DCIM suite. DCIM is what enterprises buy when they have time. Hyperscalers, colos, and AI halls do not have time. They buy **time-to-production** and **truth of inventory**.

Three facts make this a board-level positioning problem:

1. **AI density made the old sales motion obsolete.** A 100 kW rack is not a UPS conversation and a cooling conversation and a PDU conversation. It is one placement, one power chain, one thermal envelope, one identity. If we sell SKUs, the customer’s integrator becomes the hero. If we sell the integrated rack, we become the hero.
2. **We already paid for this lesson.** DCP drew the hall. DSView touched the hall. Environet watched facilities. We discontinued the map and kept the pieces. Competitors did not beat our hardware. They beat our **story**. Sunbird says “see the hall.” nlyte says “govern the hall.” We still say “here are the products.”
3. **Software is how hardware gets specified.** The team that owns inventory, auto-config, and monitoring writes the BOM. If that team is Sunbird plus a SI, Vertiv is a line item. If that team is Vertiv, the PDU, the rack manager, the UPS, and the rear door are the default.

**Do not say:** “We need to get back into DCIM.”
**Do say:** “We need to own Find, Configure, and Watch on the metal we already ship.”

---

## 2. The market story we should steal — then own

**Talk:**

Four products already taught the market what “good” looks like. We should promote against those jobs, not against those logos.

| Job the customer already understands | Who they associate with it today | What Vertiv should claim |
| --- | --- | --- |
| Draw and search the hall (space, power, ports) | DCP (us, discontinued), Sunbird | We still owe a **map**, but it must fill itself |
| Keep inventory honest, dock to decom | nlyte | We reconcile **intended vs live**; we do not run ServiceNow |
| Bulk-configure PDUs and watch kW | Sunbird Power IQ | **Native** on Geist / Vertiv PDUs — no second product |
| Hands-on when the OS is dead | DSView (us) | Keep this. Make it a **function of the asset**, not a destination |
| Rack as a finished good | Apple (private stack) | **This is the Vertiv brand claim** |

The punchline for executives:

**Sunbird shows the hall. nlyte governs the hall. DSView touches the hall. Apple integrates the hall.**

**Vertiv is the only company that can productize Apple’s method because we manufacture the power, the cooling, the PDU, and the access path.**

We are not pitching “sell to Apple.” We are pitching “sell the Apple *method* to everyone who cannot staff Apple’s software org.”

---

## 3. The promotion idea in one diagram

**Talk (walk this):**

```
  FACTORY / INTEGRATION          THE HALL                    THE NOC
  ─────────────────────          ────────                    ───────
  Rack ships with a              Plug in.                    Same object shows
  birth certificate:             15 minutes later            kW, inlet temp,
  what should be there           we know what IS there       SP health, KVM
                                 We apply the standard       Drift is an alarm
                                 We start watching
```

Three verbs. That is the campaign, the product, and the demo.

1. **Find** — inventory without a spreadsheet
2. **Configure** — gold-image the infrastructure (names, firmware, traps, accounts, DSView enrollment)
3. **Watch** — monitoring is a consequence of inventory, not a second project

If a press release, a sales deck, or a services SOW cannot be reduced to those three verbs, it is the old Vertiv.

---

## 4. How we should promote Vertiv (the actual GTM)

This is the heart of the meeting. Positioning, then proof, then who we say it to.

### 4.1 Reposition the brand sentence

**From:** “A global leader in critical digital infrastructure — power, cooling, and IT management.”

**To:** “Vertiv ships racks that know what they are. Power, cooling, and access arrive on one identity: found, configured, and monitored before the customer opens a ticket.”

Shorter campaign line:

> **The rack that inventories itself.**

Alt lines (pick one, kill the rest):

- **Don’t integrate Vertiv. Plug it in.**
- **From crate to telemetry in one pass.**
- **Intended. Live. Watched. One asset.**

### 4.2 Stop promoting brands. Promote the loop.

Today we promote Liebert, Geist, Avocent, Vertiv as if the customer enjoys brand archaeology.

**New rule:** In executive and AI-hall conversations, the brand is Vertiv. The SKUs are evidence. DSView is not a product we lead with; it is how you launch a session on an asset we already found. Environet is not a product we lead with; it is how facilities points show up on that same asset.

Keep the heritage names in the install base and in the BOM. Do not make the customer assemble our org chart.

### 4.3 Lead with a demo, not a portfolio

The promotion that will move a CIO or a colo COO is not a three-layer architecture slide. It is this:

1. Scan a QR on the rack. Intended state appears.
2. Power it. Live inventory fills in under 15 minutes.
3. One click applies the standard.
4. kW, temperature, and health are already on.
5. Something is wrong in U12. Drift lights up. Launch KVM from that same screen.

If we cannot demo that, we should not yet spend big-campaign money. **The demo is the promotion.** Until it exists, the executive message is “this is the hill,” not “this is generally available.”

### 4.4 Who we talk to — and what we say

| Buyer | What they fear | Vertiv line |
| --- | --- | --- |
| **Hyperscale / AI lab / national cloud** | Mystery inventory, slow turn-up, firmware drift | “Your rack leaves our world with a birth certificate. Your hall only verifies and watches.” |
| **Colo** | Tenant turn-up cost, stranded power, truck rolls | “Cabinet live in minutes. Actual vs budget on day one. Hands-on without a flight.” |
| **Enterprise CIO** | Spreadsheets, audit failure, too many tools | “One identity for the asset. Your ServiceNow can subscribe. You don’t start another DCIM religion.” |
| **Consultants / SIs** | Being disintermediated | “You design the hall and the standard. We execute Find → Configure → Watch so you stop typing serials.” |

**Do not lead with:** PUE widgets, 3D digital twins, “single pane of glass.”
**Do lead with:** minutes-to-inventory, policy pack, no second wizard.

### 4.5 What we attach the story to commercially

Promotion without an offer is a keynote. Attach the new story to things we can sell **now**, then to the platform:

| Horizon | What we promote | Commercial motion |
| --- | --- | --- |
| **Now** | Vertiv rack as the unit of sale (frame + PDU + rack manager + thermal option) | Configure-to-order includes a **digital birth certificate** even if software is still thin |
| **Now** | DSView Solution + Geist PDU as “the rack is visible and controllable” | Bundle, don’t cross-sell as an afterthought |
| **Next** | Find → Configure → Watch platform (see requirements doc) | Subscription on the rack, not another perpetual DCIM |
| **Always** | Services as **exceptions**, not as the integration tax | If services are required to type inventory, the product failed |

The executive point: **we can start promoting the idea on the next configure-to-order rack**, before the full platform lands. Ship the birth certificate with the hardware. That is a factory change and a sales change, not a two-year rewrite.

### 4.6 Competitive posture (how we talk about others)

Never trash Sunbird or nlyte in the room. They trained the customer.

- **Sunbird:** “They made inventory usable. We agree. We will match that usability and go further: the inventory is born in our factory and the PDU configures itself because we make it.”
- **nlyte:** “They made reconciliation and workflow real. We will not try to be ServiceNow. We will be the live truth those systems subscribe to.”
- **Schneider / Eaton software:** “They also make hardware. The race is who closes the loop. We have Avocent. That is the control plane they do not have.”
- **Apple:** “We are not pretending to be Apple. We are productizing the operating model everyone already wishes they had.”

### 4.7 Internal promotion — this is half the job

If sales still opens with UPS efficiency and CRAC SKUs, the external campaign will bounce.

Ask ELT to enforce four internal rules:

1. **AI and colo deals open with the rack loop**, then the SKUs.
2. **Software is not an attach rate.** It is how the hardware is specified.
3. **No slide that lists five Vertiv consoles** as a customer benefit.
4. **Services quotes that include “we will build your asset database”** are a product bug, not a revenue opportunity.

---

## 5. Why now

**Talk:**

Three clocks are running.

- **AI halls are being designed this year.** Liquid, 100 kW+, busway, rear doors. The designer who owns the digital twin of that rack owns the vendor list. If we are late, we are a cooling vendor in someone else’s model.
- **We already exited the map.** Every quarter without a replacement, Sunbird and nlyte become the default “system of record” language in RFPs we did not write.
- **DSView Solution is the kernel we still have.** REST, Redfish, Geist, HTML5 KVM. If we do not make it the discovery sensor for a hall-level story, it stays a niche access tool and we will eventually be asked why we still own Avocent.

Waiting looks prudent. It is how we lost DCP’s job without losing DCP’s hardware.

---

## 6. Risks executives will raise — answer them here

**“We tried DCIM. Trellis died.”**
Trellis was a suite that asked customers to become a program. This is a power-on contract for a rack. Different product, different buyer, different time-to-value. If it needs an 18-month professional-services engagement, we will have failed in the same way and we should kill it.

**“We will pick a fight with Sunbird and nlyte.”**
Only if we try to replace their entire install base on day one. The adult move is coexistence: we are the live identity and the actuator; they can remain the CMDB or the BI layer. Conquest is optional. **Being absent from the inventory conversation is not.**

**“Software margins vs hardware.”**
The point is not to become a software company. The point is to **protect hardware specification**. A subscription on the rack is a bonus. Losing the PDU and rack manager because someone else’s DCIM prefers another vendor is the real margin event.

**“Apple will never buy this.”**
Correct. They will not. The buyers are everyone who wants Apple’s operational hygiene and cannot write it. That is colo, enterprise, government, and the AI builders who are not hyperscalers yet.

**“This dilutes the power and cooling brand.”**
It concentrates it. Power and cooling that cannot be found, named, and watched are commodities. Power and cooling on a verified identity are infrastructure.

---

## 7. The ask (close on this)

**Talk:**

I need three decisions, not a task force.

1. **Positioning.** Adopt the public sentence: *Vertiv does not ask you to integrate us. We arrive already integrated.* Use it in AI, colo, and executive narratives starting now. Retire “single pane of glass.”
2. **Proof.** Fund the Section 14 demo in the requirements document: one rack, QR to telemetry in 15 minutes, KVM from the same asset. That demo is the campaign. No brand spend until it is real — except the factory birth certificate on configure-to-order racks, which we can start without new software.
3. **Ownership.** Name one executive owner for Find → Configure → Watch across Avocent, Geist, thermal, and Environet. If it stays in three business units, we will promote three products again.

If we do those three things, we stop being a well-respected catalog and start being the company that turns a crate into a known, standard, watched rack.

That is how Apple would promote us, if they had to buy us. We should not wait for them to build it themselves.

---

## 8. One-pager to leave in the room

| | |
| --- | --- |
| **Problem** | We manufacture the hall. We promote SKUs. Customers hire someone else to integrate us. |
| **Shift** | Promote the **rack loop**: Find → Configure → Watch. |
| **Proof point** | Birth certificate at ship. Live inventory in minutes. Policy pack. Monitoring with no second wizard. DSView as hands, not a destination. |
| **Why Vertiv** | We make the PDU, the access path, the UPS, and the cooling. Nobody else can close that loop without a SI. |
| **Not doing** | Rebuilding Trellis. Competing with ServiceNow. Leading with 3D twins. |
| **Ask** | Positioning + demo + single owner. |

---

## Appendix — 12-minute run of show

| Min | Block | Outcome |
| --- | --- | --- |
| 0–1 | Opening | “We arrive already integrated.” |
| 1–3 | Why it’s executive | AI rack, lost map, software specifies hardware |
| 3–5 | Market jobs | Sunbird / nlyte / DSView / Apple — then our claim |
| 5–8 | How we promote | Brand sentence, demo, buyers, attach to CTO racks |
| 8–10 | Why now + risks | Trellis objection, coexistence, specification |
| 10–12 | Ask | Positioning, demo, owner |
| 12+ | Discussion | Fill the decision record in the requirements doc |

**If you only get five minutes:** say the opening, the three verbs, the demo, and the three asks. Sit down.
