"""
Streamlit app with a Supabase (PostgreSQL) backend.

Table schema (already created in Supabase):
    user_details
        USER_ID  int4  primary key   (assumed identity / auto-increment)
        NAME     text
        POB      text
        PH_NUM   text
        MAIL_ID  text

Requirements:
    pip install streamlit supabase pandas

Run:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# -----------------------------------------------------------------------------
# Supabase configuration -- replace these with your own values
# -----------------------------------------------------------------------------
SUPABASE_URL: str = "https://xfonthspghahbqvbtmdh.supabase.co"      # e.g. "https://xxxx.supabase.co"
SUPABASE_KEY: str = "sb_publishable_lS84lnDCzUJSbIjrUAC8aw_gq4QCCfq"      # anon or service-role key
TABLE_NAME: str = "user_details"


@st.cache_resource
def get_supabase_client() -> Client:
    """Create and cache a single Supabase client for the session."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_user(supabase: Client, payload: dict) -> dict | None:
    """Insert a row into user_details. Returns the inserted row, or None on error."""
    try:
        response = supabase.table(TABLE_NAME).insert(payload).execute()
        return response.data[0] if response.data else None
    except Exception as exc:
        st.error(f"Failed to save record: {exc}")
        return None


def fetch_users(supabase: Client) -> list[dict]:
    """Fetch all rows from user_details, newest first (by USER_ID)."""
    try:
        response = (
            supabase.table(TABLE_NAME)
            .select("*")
            .order("USER_ID", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        st.error(f"Failed to load records: {exc}")
        return []


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.set_page_config(page_title="User Details", page_icon="📝", layout="centered")
st.title("📝 User Details")
st.caption("Submit the form below — entries are stored in Supabase and listed underneath.")

supabase = get_supabase_client()

with st.form("user_form", clear_on_submit=True):
    st.subheader("Add a new user")

    name = st.text_input("Name *", placeholder="Jane Doe")
    pob = st.text_input("Birth Place *", placeholder="London, UK")
    ph_num = st.text_input("Phone", placeholder="+1 555 123 4567")
    mail_id = st.text_input("Email", placeholder="jane@example.com")

    submitted = st.form_submit_button("Save")

    if submitted:
        if not name.strip() or not pob.strip():
            st.warning("Name and Birth Place are required.")
        else:
            # USER_ID is omitted — Supabase will assign it if the column is set
            # as an identity / auto-increment primary key. If your USER_ID is a
            # plain int4 with no default, you'll need to generate it yourself
            # (e.g. max(USER_ID) + 1) before inserting.
            payload = {
                "NAME": name.strip(),
                "POB": pob.strip(),
                "PH_NUM": ph_num.strip() or None,
                "MAIL_ID": mail_id.strip() or None,
            }
            inserted = insert_user(supabase, payload)
            if inserted:
                st.success(f"Saved {inserted.get('NAME', name)} ✅")

# -----------------------------------------------------------------------------
# Records table
# -----------------------------------------------------------------------------
st.divider()
st.subheader("Saved records")

records = fetch_users(supabase)

if not records:
    st.info("No records yet. Add one using the form above.")
else:
    df = pd.DataFrame(records)

    # Order/limit columns for a tidy display
    preferred_cols = ["USER_ID", "NAME", "POB", "PH_NUM", "MAIL_ID"]
    display_cols = [c for c in preferred_cols if c in df.columns]
    df = df[display_cols]

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(df)} record(s) total.")
