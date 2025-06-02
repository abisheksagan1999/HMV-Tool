import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import fuzz
import difflib

# Load Excel data
@st.cache_data
def load_data():
    df = pd.read_excel("hmv_data.xlsx")
    df.dropna(subset=["Description", "Corrective Action", "Total Hours"], inplace=True)
    return df

df = load_data()

st.title("🛠️ Historical Maintenance Hours Checker")

# User Inputs
desc_input = st.text_input("Enter Discrepancy / Description:")
corr_input = st.text_input("Enter Corrective Action:")

# Helper functions
def normalize(text):
    text = str(text).upper()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def highlight_diff(base, comp):
    seq = difflib.SequenceMatcher(None, base.split(), comp.split())
    result = ""
    for opcode, a1, a2, b1, b2 in seq.get_opcodes():
        if opcode == 'equal':
            result += ' ' + ' '.join(comp.split()[b1:b2])
        elif opcode in ['replace', 'insert']:
            result += ' <span style="color:red">' + ' '.join(comp.split()[b1:b2]) + '</span>'
    return result.strip()

# Search logic
if desc_input and corr_input:
    norm_desc = normalize(desc_input)
    norm_corr = normalize(corr_input)

    # Exact Match
    exact_matches = df[
        (df['Description'].apply(normalize) == norm_desc) &
        (df['Corrective Action'].apply(normalize) == norm_corr)
    ]

    st.subheader("📌 Exact Match")
    if not exact_matches.empty:
        most_common_hours = exact_matches['Total Hours'].mode()[0]
        st.success(f"✅ Found {len(exact_matches)} exact match(es)")
        st.write(f"Historical Hours: **{most_common_hours}**")
        st.write(f"Suggested Fair Quote (99%): **{int(most_common_hours * 0.99)} hours**")
        st.dataframe(exact_matches[['Orig. Card #', 'Ref #', 'Year', 'Total Hours']])
    else:
        st.warning("❌ No exact match found.")

    # Approximate Matches
    st.subheader("🔍 Approximate Matches")

    df['Description_Score'] = df['Description'].apply(lambda x: fuzz.token_sort_ratio(norm_desc, normalize(x)))
    df['Corrective_Score'] = df['Corrective Action'].apply(lambda x: fuzz.token_sort_ratio(norm_corr, normalize(x)))
    df['Combined_Score'] = (df['Description_Score'] + df['Corrective_Score']) / 2

    approx_matches = df[df['Combined_Score'] >= 90].sort_values(by='Combined_Score', ascending=False).head(5)

    if not approx_matches.empty:
        for _, row in approx_matches.iterrows():
            desc_highlight = highlight_diff(norm_desc, normalize(row['Description']))
            corr_highlight = highlight_diff(norm_corr, normalize(row['Corrective Action']))
            st.markdown(f"**Discrepancy:** {desc_highlight}", unsafe_allow_html=True)
            st.markdown(f"**Corrective Action:** {corr_highlight}", unsafe_allow_html=True)
            st.write(f"Total Hours: **{row['Total Hours']}**, Year: {row['Year']}, Card #: {row['Orig. Card #']}")
            st.markdown("---")
    else:
        st.info("No close matches found.")
