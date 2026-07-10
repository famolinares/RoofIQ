from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from roofiq.core import (
    apply_filters,
    enrich_properties,
    load_property_file,
    summarize,
)

st.set_page_config(page_title="RoofIQ", page_icon="🏠", layout="wide")

st.title("RoofIQ")
st.caption("South Florida roof prospecting and direct-mail preparation")

with st.sidebar:
    st.header("1. Import data")
    uploaded = st.file_uploader(
        "Upload the enriched county property file",
       