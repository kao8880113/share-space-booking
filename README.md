# share-space-booking

地域のシェアスペース予約サイト。Streamlit + SQLite で作られたシンプルな予約管理アプリです。

## 主な機能

- カレンダー形式で日ごとの空き状況を表示（空き / 残りわずか / 満室 / 受付終了）
- 日付と時間帯（1時間単位）を選んで予約フォームに入力（名前・連絡先・利用目的）
- 予約するとその場で予約一覧に反映される
- 予約一覧はキーワード検索・絞り込み・キャンセルに対応
- シンプルで見やすいデザイン（グリーン基調のカード型UI）

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 起動方法

```bash
source .venv/bin/activate
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開き、予約サイトが表示されます。

## データの保存先

予約データはリポジトリ直下の `bookings.db`（SQLite）に保存されます。このファイルは `.gitignore` で管理対象外にしているため、Git 履歴には含まれません。

## 設定の変更

`app.py` 冒頭の定数で調整できます。

- `ROOM_NAME`: スペース名
- `OPEN_HOUR` / `CLOSE_HOUR`: 受付時間帯
- `PURPOSE_OPTIONS`: 利用目的の選択肢
