[← Back to README](../README.md)

# Safety & Compliance

## Safety Analysis

| Hazard | Risk Level | Likelihood | Mitigation Measure |
| --- | --- | --- | --- |
| Mains AC shock from cooling-tower motor circuit (SSR output stage) | **High** | Possible | Solid-state relay (SSR) provides full electrical isolation between the 5 V microcontroller logic and the AC line; no exposed mains contacts on the control PCB |
| Overvoltage / transient spikes on DC rails (12 V adapter input, regulator stage) | **Medium** | Possible | L7805/L7808 linear regulators with input/output decoupling capacitors and ferrite beads to filter input transients |
| Short circuit / overcurrent on regulated 5 V/8 V rails (PCB 1, PCB 2) | **Medium** | Unlikely | Resettable fuse on the DC input line; regulator built-in thermal shutdown and current-limiting protection |
| Water ingress damaging electronics (rooftop enclosure, water-spray exposure) | **High** | Possible | IP54-rated PETG enclosure, sealed cable entry ports, gasketed removable lid for maintenance access |
| UV exposure and thermal degradation of enclosure material (rooftop, direct sunlight) | **Low** | Likely | PETG selected for UV resistance and a heat-deflection temperature of approximately 70–80 °C, suited to Sri Lankan rooftop conditions |
| RF interference with other 433 MHz ISM-band devices (LoRa SX1278 link) | **Low** | Unlikely | Low duty-cycle transmission, spread-spectrum LoRa modulation, and compliant transmit power levels |
| Mechanical injury during installation or maintenance (pole-clamp mounting) | **Low** | Unlikely | Non-destructive pole-clamp mounting; enclosure lid accessible without disturbing live AC wiring |

## Applicable Standards

- **IEC 60529 (IP Rating)** – Defines the IP54 dust and water ingress protection target specified for both the rooftop and ground-station enclosures
- **ITU-R / FCC Part 15 (433 MHz ISM Band)** – Governs unlicensed short-range RF transmit power and duty-cycle limits applicable to the LoRa SX1278 communication module
- **Telecommunications Regulatory Commission of Sri Lanka (TRCSL)** – Local equipment type-approval requirements for the 433 MHz radio module, applicable since the system is deployed within Sri Lanka
