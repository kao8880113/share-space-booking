"""
地域のシェアスペース予約サイト
Streamlit + SQLite で作成したシンプルな予約管理アプリ。
"""

import calendar
import sqlite3
import uuid
from contextlib import closing
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# 基本設定
# ----------------------------------------------------------------------------
DB_PATH = "bookings.db"
ROOM_NAME = "地域シェアスペース"
OPEN_HOUR = 9           # 開館時間
CLOSE_HOUR = 21         # 閉館時間
SLOTS = [(h, h + 1) for h in range(OPEN_HOUR, CLOSE_HOUR)]  # 1時間単位のコマ
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]
PURPOSE_OPTIONS = [
    "会議・打ち合わせ",
    "サークル・趣味活動",
    "勉強会・セミナー",
    "イベント・催し物",
    "地域交流",
    "その他",
]

st.set_page_config(
    page_title=f"{ROOM_NAME} 予約サイト",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# スタイル（シンプルで見やすいデザイン）
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        :root {
            --brand: #2f9e6e;
            --brand-light: #e6f5ee;
            --danger: #e0563f;
            --danger-light: #fdecea;
            --muted: #94a3b8;
        }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1080px; }
        h1, h2, h3 { color: #1f2937; }
        .app-header {
            padding: 1.1rem 1.4rem;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--brand) 0%, #56c596 100%);
            color: white;
            margin-bottom: 1.4rem;
        }
        .app-header h1 { color: white; margin: 0; font-size: 1.5rem; }
        .app-header p { margin: 0.2rem 0 0 0; opacity: 0.92; font-size: 0.92rem; }

        .cal-cell {
            border-radius: 10px;
            padding: 0.4rem 0.2rem;
            text-align: center;
            font-size: 0.82rem;
            border: 1px solid #e5e7eb;
        }
        .cal-cell.today { border: 2px solid var(--brand); }
        .cal-cell .day-num { font-weight: 700; font-size: 0.95rem; }
        .cal-badge {
            display: inline-block;
            margin-top: 3px;
            padding: 1px 7px;
            border-radius: 999px;
            font-size: 0.68rem;
            font-weight: 600;
        }
        .badge-free { background: var(--brand-light); color: var(--brand); }
        .badge-few  { background: #fff4e0; color: #b8710b; }
        .badge-full { background: var(--danger-light); color: var(--danger); }
        .badge-past { background: #f1f5f9; color: var(--muted); }

        .slot-free { color: #1f2937; }
        .slot-booked { color: var(--muted); text-decoration: line-through; }

        .booking-card {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.6rem;
            background: #fafafa;
        }
        .stButton>button {
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# DB 関連
# ----------------------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_connection()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                start_hour INTEGER NOT NULL,
                end_hour INTEGER NOT NULL,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                purpose TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def get_bookings_for_date(date_str: str):
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE date = ? ORDER BY start_hour",
            (date_str,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_booked_hours(date_str: str) -> set:
    booked = set()
    for b in get_bookings_for_date(date_str):
        booked.update(range(b["start_hour"], b["end_hour"]))
    return booked


def get_month_booked_counts(year: int, month: int) -> dict:
    """その月の日付ごとの予約済みコマ数を返す"""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT date, start_hour, end_hour FROM bookings WHERE date BETWEEN ? AND ?",
            (first_day.isoformat(), last_day.isoformat()),
        ).fetchall()
    counts = {}
    for r in rows:
        counts[r["date"]] = counts.get(r["date"], 0) + (r["end_hour"] - r["start_hour"])
    return counts


def add_booking(date_str, start_hour, end_hour, name, contact, purpose):
    with closing(get_connection()) as conn:
        conn.execute(
            """
            INSERT INTO bookings (id, date, start_hour, end_hour, name, contact, purpose, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4())[:8],
                date_str,
                start_hour,
                end_hour,
                name,
                contact,
                purpose,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def delete_booking(booking_id: str):
    with closing(get_connection()) as conn:
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()


def get_all_bookings_df() -> pd.DataFrame:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT * FROM bookings ORDER BY date, start_hour"
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    return df


init_db()

# ----------------------------------------------------------------------------
# セッション状態
# ----------------------------------------------------------------------------
today = date.today()
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month
if "selected_date" not in st.session_state:
    st.session_state.selected_date = today
if "just_booked" not in st.session_state:
    st.session_state.just_booked = False

# ----------------------------------------------------------------------------
# ヘッダー
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="app-header">
        <h1>🏠 {ROOM_NAME} 予約サイト</h1>
        <p>カレンダーから空き状況を確認して、日付と時間帯を選んで予約できます。（受付時間 {OPEN_HOUR}:00〜{CLOSE_HOUR}:00）</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_book, tab_list = st.tabs(["📅 予約する", "📋 予約一覧"])

# ----------------------------------------------------------------------------
# タブ1: 予約する（カレンダー + フォーム）
# ----------------------------------------------------------------------------
with tab_book:
    col_cal, col_form = st.columns([1.15, 1], gap="large")

    with col_cal:
        # 月移動
        nav_prev, nav_title, nav_next = st.columns([1, 3, 1])
        with nav_prev:
            if st.button("◀ 前月", use_container_width=True):
                m = st.session_state.cal_month - 1
                y = st.session_state.cal_year
                if m < 1:
                    m, y = 12, y - 1
                st.session_state.cal_month, st.session_state.cal_year = m, y
                st.rerun()
        with nav_title:
            st.markdown(
                f"<h3 style='text-align:center; margin-top:0.3rem;'>"
                f"{st.session_state.cal_year}年 {st.session_state.cal_month}月</h3>",
                unsafe_allow_html=True,
            )
        with nav_next:
            if st.button("翌月 ▶", use_container_width=True):
                m = st.session_state.cal_month + 1
                y = st.session_state.cal_year
                if m > 12:
                    m, y = 1, y + 1
                st.session_state.cal_month, st.session_state.cal_year = m, y
                st.rerun()

        year, month = st.session_state.cal_year, st.session_state.cal_month
        total_hours = len(SLOTS)
        booked_counts = get_month_booked_counts(year, month)

        # 曜日ヘッダー
        header_cols = st.columns(7)
        for i, wd in enumerate(WEEKDAY_JA):
            header_cols[i].markdown(
                f"<div style='text-align:center; font-weight:600; color:#6b7280; font-size:0.82rem;'>{wd}</div>",
                unsafe_allow_html=True,
            )

        cal = calendar.Calendar(firstweekday=0)  # 月曜始まり
        weeks = cal.monthdayscalendar(year, month)

        for week in weeks:
            cols = st.columns(7)
            for i, day_num in enumerate(week):
                with cols[i]:
                    if day_num == 0:
                        st.markdown("<div class='cal-cell' style='visibility:hidden;'>-</div>", unsafe_allow_html=True)
                        continue

                    d = date(year, month, day_num)
                    d_str = d.isoformat()
                    is_past = d < today
                    is_today = d == today
                    booked = booked_counts.get(d_str, 0)
                    remaining = total_hours - booked

                    if is_past:
                        badge_html = "<span class='cal-badge badge-past'>受付終了</span>"
                    elif remaining <= 0:
                        badge_html = "<span class='cal-badge badge-full'>満室</span>"
                    elif remaining <= 3:
                        badge_html = f"<span class='cal-badge badge-few'>残{remaining}</span>"
                    else:
                        badge_html = "<span class='cal-badge badge-free'>空き</span>"

                    cell_class = "cal-cell today" if is_today else "cal-cell"
                    st.markdown(
                        f"<div class='{cell_class}'>"
                        f"<div class='day-num'>{day_num}</div>{badge_html}</div>",
                        unsafe_allow_html=True,
                    )
                    btn_label = "選択中" if d == st.session_state.selected_date else "選ぶ"
                    disabled = is_past
                    if st.button(
                        btn_label,
                        key=f"pick_{d_str}",
                        use_container_width=True,
                        disabled=disabled,
                        type="primary" if d == st.session_state.selected_date else "secondary",
                    ):
                        st.session_state.selected_date = d
                        st.session_state.just_booked = False
                        st.rerun()

        st.markdown(
            """
            <div style="margin-top:0.6rem; font-size:0.78rem; color:#6b7280;">
                <span class="cal-badge badge-free">空き</span> 4コマ以上の空き
                <span class="cal-badge badge-few">残n</span> 残りわずか
                <span class="cal-badge badge-full">満室</span> 予約不可
                <span class="cal-badge badge-past">受付終了</span> 過去の日付
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_form:
        sel_date = st.session_state.selected_date
        sel_date_str = sel_date.isoformat()
        weekday_ja = WEEKDAY_JA[sel_date.weekday()]
        st.markdown(f"### {sel_date.year}年{sel_date.month}月{sel_date.day}日（{weekday_ja}）の予約")

        if sel_date < today:
            st.warning("過去の日付は予約できません。カレンダーから別の日を選んでください。")
        else:
            if st.session_state.just_booked:
                st.success("予約を受け付けました！左のカレンダーや「予約一覧」タブから確認できます。")
                st.session_state.just_booked = False

            booked_hours = get_booked_hours(sel_date_str)
            st.caption("予約したい時間帯にチェックを入れてください（連続した時間帯のみ選択できます）")

            with st.form("booking_form", clear_on_submit=False):
                slot_cols = st.columns(3)
                selected_slots = []
                for idx, (h, h_end) in enumerate(SLOTS):
                    is_booked = h in booked_hours
                    label = f"{h:02d}:00-{h_end:02d}:00" + ("（予約済）" if is_booked else "")
                    checked = slot_cols[idx % 3].checkbox(
                        label, key=f"slot_{sel_date_str}_{h}", disabled=is_booked
                    )
                    if checked:
                        selected_slots.append(h)

                st.markdown("---")
                name = st.text_input("お名前 *", placeholder="山田 太郎")
                contact = st.text_input("連絡先（電話番号 or メールアドレス） *", placeholder="090-1234-5678")
                purpose_select = st.selectbox("利用目的 *", PURPOSE_OPTIONS)
                purpose_detail = st.text_input("利用目的の詳細（任意）", placeholder="例：自治会の定例会議")

                submitted = st.form_submit_button("この内容で予約する", type="primary", use_container_width=True)

                if submitted:
                    errors = []
                    slots_sorted = sorted(selected_slots)

                    if not slots_sorted:
                        errors.append("時間帯を1つ以上選択してください。")
                    else:
                        is_contiguous = all(
                            slots_sorted[i] + 1 == slots_sorted[i + 1]
                            for i in range(len(slots_sorted) - 1)
                        )
                        if not is_contiguous:
                            errors.append("時間帯は連続したコマのみ選択できます（例：10:00〜12:00）。")

                    if not name.strip():
                        errors.append("お名前を入力してください。")
                    if not contact.strip():
                        errors.append("連絡先を入力してください。")

                    # 二重予約防止のため最新状態で再チェック
                    if not errors:
                        fresh_booked = get_booked_hours(sel_date_str)
                        if any(h in fresh_booked for h in slots_sorted):
                            errors.append("選択した時間帯は直前に他の方が予約しました。別の時間帯を選び直してください。")

                    if errors:
                        for e in errors:
                            st.error(e)
                    else:
                        start_hour = slots_sorted[0]
                        end_hour = slots_sorted[-1] + 1
                        purpose_value = purpose_select
                        if purpose_detail.strip():
                            purpose_value = f"{purpose_select}（{purpose_detail.strip()}）"
                        add_booking(
                            sel_date_str, start_hour, end_hour,
                            name.strip(), contact.strip(), purpose_value,
                        )
                        st.session_state.just_booked = True
                        st.rerun()

            # 当日の予約状況を一覧表示
            todays_bookings = get_bookings_for_date(sel_date_str)
            if todays_bookings:
                st.markdown("#### この日の予約状況")
                for b in todays_bookings:
                    st.markdown(
                        f"<div class='booking-card'>"
                        f"🕒 {b['start_hour']:02d}:00-{b['end_hour']:02d}:00　"
                        f"<b>{b['name']}</b>　"
                        f"<span style='color:#6b7280;'>{b['purpose']}</span></div>",
                        unsafe_allow_html=True,
                    )

# ----------------------------------------------------------------------------
# タブ2: 予約一覧
# ----------------------------------------------------------------------------
with tab_list:
    st.markdown("### 予約一覧")

    df = get_all_bookings_df()
    if df.empty:
        st.info("まだ予約はありません。")
    else:
        df["時間帯"] = df.apply(
            lambda r: f"{r['start_hour']:02d}:00-{r['end_hour']:02d}:00", axis=1
        )
        df_display = df.rename(
            columns={
                "date": "日付",
                "name": "お名前",
                "contact": "連絡先",
                "purpose": "利用目的",
                "id": "予約ID",
            }
        )[["予約ID", "日付", "時間帯", "お名前", "連絡先", "利用目的"]]

        colf1, colf2 = st.columns([1, 1])
        with colf1:
            show_upcoming_only = st.checkbox("今日以降の予約のみ表示", value=True)
        with colf2:
            keyword = st.text_input("お名前・目的で検索", placeholder="キーワードを入力")

        filtered = df_display.copy()
        if show_upcoming_only:
            filtered = filtered[filtered["日付"] >= today.isoformat()]
        if keyword.strip():
            kw = keyword.strip()
            filtered = filtered[
                filtered["お名前"].str.contains(kw, case=False, na=False)
                | filtered["利用目的"].str.contains(kw, case=False, na=False)
            ]

        filtered = filtered.sort_values(["日付", "時間帯"]).reset_index(drop=True)
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption(f"該当件数: {len(filtered)}件")

        with st.expander("予約をキャンセルする"):
            st.caption("上記の表で「予約ID」を確認し、キャンセルしたい予約IDを選択してください。")
            if not filtered.empty:
                cancel_id = st.selectbox("キャンセルする予約ID", filtered["予約ID"].tolist())
                if st.button("この予約をキャンセルする", type="secondary"):
                    delete_booking(cancel_id)
                    st.success("予約をキャンセルしました。")
                    st.rerun()
            else:
                st.write("キャンセルできる予約がありません。")
