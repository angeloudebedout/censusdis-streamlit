# streamlit_app.py

import backend as be
import visualizations as viz
import ui_helpers as ui
import data.census_vars as cv
import streamlit as st

# Page layout & header
st.set_page_config(layout="wide")
st.header("How has America Changed Since Covid?")
st.write(open("text/intro.md").read())

# --- User input selectors ---
state_col, county_col, demographic_col = st.columns(3)

with state_col:
    state = st.selectbox("State:", be.get_states(), index=4)  # default California
    county_index = ui.get_county_index(state)

with county_col:
    county = st.selectbox("County:", be.get_counties(state), index=county_index)
    full_name = ", ".join([county, state])

with demographic_col:
    var = st.selectbox("Demographic:", cv.census_dropdown_values)

# Years to compare (hardcoded)
YEAR1 = "2019"
YEAR2 = "2023"

# Tabs for views
graph_tab, table_tab, map_tab, about_tab = st.tabs(
    ["📈 Graphs", "🔍 Table", "🗺️ Map", "ℹ️ About"]
)

# --- Graph tab ---
with graph_tab:
    line_col, swarm_col = st.columns(2)

    with line_col:
        fig_line = viz.get_line_graph(full_name, var)
        st.pyplot(fig_line)
        st.write("*Dashed line indicates missing data for 2020.*")

    with swarm_col:
        fig_swarm = viz.get_swarmplot(var, YEAR1, YEAR2, full_name)
        st.pyplot(fig_swarm)
        swarm_text = open("text/swarmplot.md").read().format(var=var)
        st.write(swarm_text)

# --- Table tab ---
with table_tab:
    ranking_df = be.get_ranking_df(var, YEAR1, YEAR2, False)
    ranking_text = be.get_ranking_text(full_name, var, ranking_df)
    styled = ranking_df.style.pipe(ui.apply_styles, full_name, YEAR1, YEAR2)

    table_md = (
        open("text/table.md")
        .read()
        .format(var=var, year1=YEAR1, year2=YEAR2, ranking_text=ranking_text)
    )
    st.markdown(table_md)
    st.dataframe(styled)

# --- Map tab ---
with map_tab:
    map_text = open("text/map.md").read().format(var=var)
    st.write(map_text)
    fig_map = viz.get_map(var, YEAR1, YEAR2)
    st.plotly_chart(fig_map, use_container_width=True)

# --- About tab ---
with about_tab:
    st.write(open("text/about.md").read())
