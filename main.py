import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import altair as _alt  # type: ignore[import]
import pandas as pd
import streamlit as st

alt: Any = _alt

DATA_DIR = Path(__file__).resolve().parent / "data"


TEXT_PLACEHOLDER = "ここに入力してください"


def _ensure_state() -> None:
    # Keep generated row identifiers in session state so widgets survive reruns.
    DATA_DIR.mkdir(exist_ok=True)
    if "row_ids" not in st.session_state:
        st.session_state.row_ids = []
    if "next_row_id" not in st.session_state:
        st.session_state.next_row_id = 0
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()
    if "active_date" not in st.session_state:
        st.session_state.active_date = None
    if not st.session_state.row_ids:
        _add_row()


def _add_row(text: str = "", slider: int = 0) -> None:
    row_id = st.session_state.next_row_id
    st.session_state.next_row_id += 1
    st.session_state.row_ids.append(row_id)
    st.session_state[f"text_{row_id}"] = text
    st.session_state[f"slider_{row_id}"] = int(slider)


def _as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _clear_rows() -> None:
    for row_id in st.session_state.row_ids:
        st.session_state.pop(f"text_{row_id}", None)
        st.session_state.pop(f"slider_{row_id}", None)
    st.session_state.row_ids = []
    st.session_state.next_row_id = 0


def _reset_rows(entries: list[dict[str, object]]) -> None:
    _clear_rows()
    if not entries:
        entries = [{"text": "", "slider": 0}]
    for entry in entries:
        _add_row(
            str(entry.get("text", "")),
            _as_int(entry.get("slider", 0)),
        )


def _current_entries() -> list[dict[str, object]]:
    return [
        {
            "text": st.session_state.get(f"text_{row_id}", ""),
            "slider": _as_int(st.session_state.get(f"slider_{row_id}", 0)),
        }
        for row_id in st.session_state.row_ids
    ]


def _data_file_for_date(day: date) -> Path:
    return DATA_DIR / f"{day.isoformat()}.json"


def _load_entries_for_date(day: date) -> None:
    file_path = _data_file_for_date(day)
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as handle:
            try:
                entries = json.load(handle)
                if not isinstance(entries, list):
                    entries = []
            except json.JSONDecodeError:
                entries = []
    else:
        entries = []
    _reset_rows(entries)


def _save_entries_for_date(day: date, entries: list[dict[str, object]]) -> None:
    file_path = _data_file_for_date(day)
    payload = [
        {
            "text": str(entry.get("text", "")),
            "slider": _as_int(entry.get("slider", 0)),
        }
        for entry in entries
    ]
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def _read_entries_from_disk(day: date) -> list[dict[str, object]]:
    file_path = _data_file_for_date(day)
    if not file_path.exists():
        return []
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def main() -> None:
    st.set_page_config(page_title="Benkyo Controls", layout="wide")

    _ensure_state()

    selected_date = st.date_input("日付", value=st.session_state.selected_date)
    st.session_state.selected_date = selected_date

    previous_date = st.session_state.active_date
    if previous_date is None:
        _load_entries_for_date(selected_date)
        st.session_state.active_date = selected_date
    elif previous_date != selected_date:
        _save_entries_for_date(previous_date, _current_entries())
        _load_entries_for_date(selected_date)
        st.session_state.active_date = selected_date

    tab_inputs, tab_chart = st.tabs(["入力", "集計"])
    entries: list[dict[str, object]] = []

    with tab_inputs:
        progress_container = st.container()

        if st.button("Add", type="primary"):
            _add_row()

        slider_count = len(st.session_state.row_ids)
        target_total = slider_count * 100 if slider_count else 0
        total_slider = sum(
            _as_int(st.session_state.get(f"slider_{row_id}", 0))
            for row_id in st.session_state.row_ids
        )
        progress_value = (
            total_slider / target_total if target_total else 0.0
        )  # Normalize against combined slider max.
        with progress_container:
            st.progress(
                value=min(progress_value, 1.0),
                text=f"スライダー合計: {total_slider} / {max(target_total, 100)}",
            )
            if slider_count and total_slider == target_total:
                st.success("すべてのスライダーが最大値になりました。")
                st.balloons()
            elif slider_count:
                st.caption("各スライダーの合計が最大値になるように調整してください。")

        rows_to_remove: list[int] = []

        for index, row_id in enumerate(st.session_state.row_ids):
            label_visibility = "visible" if index == 0 else "collapsed"
            text_key = f"text_{row_id}"
            slider_key = f"slider_{row_id}"

            col_delete, col_text, col_slider = st.columns([0.2, 3, 1])
            if col_delete.button("✕", key=f"delete_{row_id}"):
                rows_to_remove.append(row_id)

            col_text.text_input(
                "テキスト",
                key=text_key,
                placeholder=TEXT_PLACEHOLDER,
                label_visibility=label_visibility,
            )
            col_slider.slider(
                "スライダー",
                min_value=0,
                max_value=100,
                value=st.session_state[slider_key],
                key=slider_key,
                label_visibility=label_visibility,
            )

        if rows_to_remove:
            for row_id in rows_to_remove:
                if row_id in st.session_state.row_ids:
                    st.session_state.row_ids.remove(row_id)
                    st.session_state.pop(f"text_{row_id}", None)
                    st.session_state.pop(f"slider_{row_id}", None)
            if not st.session_state.row_ids:
                _add_row()

        st.divider()
        st.write(f"選択した日付: {selected_date.isoformat()}")

        entries = _current_entries()
        st.write("現在の入力:")
        st.json(entries)

    _save_entries_for_date(selected_date, entries)

    with tab_chart:
        st.subheader("1週間のスライダー推移")
        start_day = selected_date - timedelta(days=6)
        week_days = [start_day + timedelta(days=offset) for offset in range(7)]
        week_labels = [day.isoformat() for day in week_days]

        daily_entries = {
            label: _read_entries_from_disk(day)
            for day, label in zip(week_days, week_labels)
        }

        max_length = 0
        label_cache: dict[int, str] = {}
        for label, day_entries in daily_entries.items():
            max_length = max(max_length, len(day_entries))
            for index, item in enumerate(day_entries):
                text_label = str(item.get("text", "")).strip()
                if text_label and index not in label_cache:
                    label_cache[index] = text_label

        if max_length == 0:
            st.info("表示できるデータがありません。")
            return

        records = []
        for index in range(max_length):
            slider_label = label_cache.get(index, f"スライダー{index + 1}")
            for day, label in zip(week_days, week_labels):
                day_entries = daily_entries.get(label, [])
                value = (
                    _as_int(day_entries[index].get("slider", 0))
                    if index < len(day_entries)
                    else 0
                )
                records.append(
                    {
                        "日付": label,
                        "スライダー": slider_label,
                        "値": value,
                    }
                )

        df = pd.DataFrame(records)
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("日付:N", sort=week_labels),
                y=alt.Y("値:Q", stack="zero"),
                color="スライダー:N",
                order="スライダー:N",
            )
            .properties(height=400)
        )
        st.altair_chart(chart, use_container_width=True)


if __name__ == "__main__":
    main()
