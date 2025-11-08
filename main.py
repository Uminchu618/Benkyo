from datetime import date

import streamlit as st


TEXT_PLACEHOLDER = "ここに入力してください"


def _ensure_state() -> None:
    # Keep generated row identifiers in session state so widgets survive reruns.
    if "row_ids" not in st.session_state:
        st.session_state.row_ids = []
    if "next_row_id" not in st.session_state:
        st.session_state.next_row_id = 0
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()
    if not st.session_state.row_ids:
        _add_row()


def _add_row() -> None:
    row_id = st.session_state.next_row_id
    st.session_state.next_row_id += 1
    st.session_state.row_ids.append(row_id)
    st.session_state[f"text_{row_id}"] = ""
    st.session_state[f"slider_{row_id}"] = 0


def main() -> None:
    st.set_page_config(page_title="Benkyo Controls", layout="wide")

    st.title("テキストとスライダー")
    _ensure_state()

    selected_date = st.date_input("日付", value=st.session_state.selected_date)
    st.session_state.selected_date = selected_date

    progress_container = st.container()

    if st.button("Add", type="primary"):
        _add_row()

    slider_count = len(st.session_state.row_ids)
    target_total = slider_count * 100 if slider_count else 0
    total_slider = sum(
        st.session_state.get(f"slider_{row_id}", 0)
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

    st.divider()

    st.write(f"選択した日付: {st.session_state.selected_date.isoformat()}")

    entries = [
        {
            "text": st.session_state[f"text_{row_id}"],
            "slider": st.session_state[f"slider_{row_id}"],
        }
        for row_id in st.session_state.row_ids
    ]
    st.write("現在の入力:")
    st.json(entries)


if __name__ == "__main__":
    main()
