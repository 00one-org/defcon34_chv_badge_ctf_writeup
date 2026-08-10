# DEF CON 34 Car Hacking Village バッジCTF Writeup

終了済みのDEF CON 34 Car Hacking VillageバッジCTFについて、実機で確認した3問の解法と再現用Pythonスクリプトを公開するリポジトリです。

- [日本語Writeup](WRITEUP.ja.md)
- [English Writeup](WRITEUP.md)

## 収録内容

- solve_knock_ctf.py — The Speakeasy Door
- solve_dtc_ctf.py — DTC Shuffle
- solve_cshim_ctf.py — CAN Cshim
- ctf_can.py — 共通のpython-can通信処理

FWダンプ、抽出したMicroPythonファイル、逆アセンブル結果、raw通信ログ、主催者配布物は収録していません。掲載コードと文書は本リポジトリ向けに作成したものです。

## 公開目的と責任ある利用

本リポジトリは、終了済みCTFの解析過程から得られた技術的知見とノウハウを、教育・研究・防御技術の向上に役立てる目的で公開しています。

悪意ある利用、第三者が所有・管理する機器への無許可アクセス、サービス妨害、データの破壊・窃取、またはその他の違法・有害な行為には使用しないでください。コードを実行できるのは、自分が所有・管理する対象、または所有者・管理者から明示的な許可を得た対象に限られます。

本リポジトリのMITライセンスは、第三者のシステムを攻撃する権限や、適用法・規約・イベントルールに違反する権限を与えるものではありません。利用者は、自身の行為について責任を負います。

## 検証範囲と注意

公開・練習用バッジではなく、会場で公式から貸与された実際のCTF専用バッジ実機に、許可された競技環境でUSB接続し、収録したソルバーで3問すべてのflagを取得したことを確認しています。ただし、確認した個体・FWリビジョン・ホスト環境は限られており、解析や説明が100%完全または正確である保証はありません。別リビジョンではアドレス、タイミング、プロトコルが異なる可能性があります。

CAN Cshimソルバーは、明示的な --exploit 指定時に対象RP2040の揮発RAM上のバッファ境界外書き込みとコールバック変更を行います。自分が所有・管理しているか、明示的な実行許可を得た対象以外には使用しないでください。フラッシュやファイルシステムへの書き込みは行いませんが、クラッシュや再起動の可能性があります。

本コードは無保証です。使用により生じた故障、データ消失、その他の損害について作者・コントリビューターは責任を負いません。

## 必要環境

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

SocketCANの場合はcan0などを直接指定できます。CTFバッジ内蔵USB CDC/SLCANを使う場合は、Car Hacking Villageの [chv-badgetools](https://github.com/car-hacking-village/chv_badgetools) を公式リポジトリから別途導入してください。

    git clone https://github.com/car-hacking-village/chv_badgetools.git
    .venv/bin/pip install ./chv_badgetools

この外部ツールは本リポジトリに同梱せず、本リポジトリのMITライセンス対象でもありません。

## 実行例

    .venv/bin/python solve_knock_ctf.py /dev/ttyACM1 --backend chv
    .venv/bin/python solve_dtc_ctf.py /dev/ttyACM1 --backend chv
    .venv/bin/python solve_cshim_ctf.py /dev/ttyACM1 --backend chv --exploit

デバイス名は環境に合わせて変更してください。Cshimは最初に --dry-run で送信内容を確認できます。

## AIの利用について

コード、解析補助、および文書の作成には、AIエージェントを含むAI支援ツールを使用しました。生成内容は人間が確認し、会場で公式から貸与されたCTF専用実機を使って、許可された競技環境で一通り検証しています。AI支援および限定的な実機検証であるため、誤りが残る可能性があります。

## 権利関係

本リポジトリ独自のコードと文書はMITライセンスです。チャレンジ名、製品名、イベント名などの権利は各権利者に帰属します。バッジFWや主催者配布物に対する権利を主張するものではありません。

## License

[MIT License](LICENSE)
