# DEF CON 34 Car Hacking Village Badge CTF Writeup

This repository documents three challenges from the concluded DEF CON 34 Car Hacking Village badge CTF and includes Python solvers reproduced against physical hardware.

- [English writeup](WRITEUP.md)
- [日本語Writeup](WRITEUP.ja.md)

## Contents

- solve_knock_ctf.py — The Speakeasy Door
- solve_dtc_ctf.py — DTC Shuffle
- solve_cshim_ctf.py — CAN Cshim
- ctf_can.py — shared python-can transport helpers

Firmware dumps, extracted MicroPython files, disassembly, raw traffic logs, and organizer-supplied files are not included. The code and prose here were created for this repository.

## Purpose and responsible use

This repository shares technical knowledge and practical lessons obtained while analyzing a concluded CTF. It is published for education, research, and the improvement of defensive security.

Do not use this material maliciously or to access third-party devices without authorization, disrupt services, destroy or obtain data, or perform any other unlawful or harmful activity. Run the code only against systems you own or administer, or systems for which the owner or administrator has given you explicit permission.

The licenses in this repository do not grant authorization to attack third-party systems or to violate applicable laws, terms, or event rules. You are responsible for your own actions.

## Validation and warning

At the venue, the author used an actual CTF-version badge officially loaned by the organizers—not a public or practice badge—and, within the authorized competition environment, used the included solvers to obtain all three flags. Nevertheless, only a limited hardware unit, firmware revision, and host setup were tested. The analysis and explanations are not guaranteed to be 100% complete or correct. Addresses, timing, and protocol behavior may differ on another revision.

With --exploit, the CAN Cshim solver performs an out-of-bounds write and callback modification in volatile RP2040 RAM. Use it only on a target you own or administer, or for which you have explicit authorization. It does not write flash or the filesystem, but it may crash or reset the target.

The software is provided without warranty. Authors and contributors accept no responsibility for damaged hardware, lost data, or other loss.

## Setup

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

For SocketCAN, pass an interface such as can0. For the badge's USB CDC/SLCAN interface, install Car Hacking Village's [chv-badgetools](https://github.com/car-hacking-village/chv_badgetools) separately:

    git clone https://github.com/car-hacking-village/chv_badgetools.git
    .venv/bin/pip install ./chv_badgetools

That external project is not bundled and is not covered by this repository's licenses.

## Examples

    .venv/bin/python solve_knock_ctf.py /dev/ttyACM1 --backend chv
    .venv/bin/python solve_dtc_ctf.py /dev/ttyACM1 --backend chv
    .venv/bin/python solve_cshim_ctf.py /dev/ttyACM1 --backend chv --exploit

Adjust the device path for your host. Review the Cshim frames first with --dry-run.

## Use of AI

The code, analysis workflow, and documentation were created with assistance from AI-supported development tools, including AI agents. A human reviewed the generated material and exercised the complete solve flow, within the authorized competition environment, on a CTF-version device officially loaned by the organizers at the venue. Errors may remain because this was AI-assisted work validated against a limited setup.

AI assistance does not by itself change the licensing classification below. Third-party materials are not relicensed by this repository.

## Rights

Challenge names, product names, event names, and related marks belong to their respective owners. Badge firmware, binaries, screenshots, organizer-supplied material, and other third-party materials are not covered by this repository's licenses unless explicitly stated. Rights remain with their respective owners.

## License

Copyright © 2026 00One, Inc.

Documentation, write-ups, original diagrams, and explanatory materials are licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-DOCS).

Source code, scripts, PoC code, and utility implementations are licensed under the [Apache License 2.0](LICENSE-CODE).

The licensing structure of this repository was updated on August 26, 2026. Earlier revisions that were distributed under the MIT License remain available under the license terms applicable to those revisions.
