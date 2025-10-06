# visualizations.py

import backend as be
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import plotly.express as px
import streamlit as st
import seaborn as sns

from colors import SEX, RACE, AGE, HISPANIC

# Diverging color constants
NEG_COLOR = "#d95f02"     # Red/orange for negative changes
ZERO_COLOR = "#ffffbf"    # Neutral at zero
POS_COLOR = "#1b5eab"     # Blue for positive changes


def get_color_map(demographic: str) -> dict:
    """
    Return a mapping dict for categorical demographics (SEX, RACE, AGE, HISPANIC).
    """
    return {
        "SEX": SEX,
        "RACE": RACE,
        "AGE": AGE,
        "HISPANIC": HISPANIC,
    }.get(demographic.upper(), {})


@st.cache_resource
def get_map(var: str, year1: int, year2: int):
    """
    Return a Plotly choropleth map with a diverging color scale:
    red/orange for counties with negative percent change,
    yellow at zero, blue for positive.
    """
    df = be.get_ranking_df(var, year1, year2, True)

    cmin = df["Percent Change"].min()
    cmax = df["Percent Change"].max()
    span = cmax - cmin if (cmax - cmin) != 0 else 1
    zero_norm = abs(cmin) / span

    colorscale = [
        [0.0, NEG_COLOR],
        [zero_norm, ZERO_COLOR],
        [1.0, POS_COLOR],
    ]

    fig = px.choropleth(
        df,
        geojson=be.county_map,
        locations="FIPS",
        color="Percent Change",
        color_continuous_scale=colorscale,
        range_color=(cmin, cmax),
        scope="usa",
        hover_name="Full Name",
        hover_data={"FIPS": False, "Percent Change": True},
        labels={"Percent Change": "Percent Change", "FIPS": "County"}
    )

    fig.update_layout(
        title_text=f"Percent Change of {var} between {year1} and {year2}",
        coloraxis_colorbar=dict(
            title="Percent Change",
            tickmode="array",
            tickvals=[cmin, 0, cmax],
            ticktext=[f"{cmin:.1f}", "0", f"{cmax:.1f}"]
        )
    )

    return fig


@st.cache_resource
def get_line_graph(full_name: str, var: str):
    """
    Return a matplotlib line plot of `var` over time for `full_name`,
    with year labels rotated to avoid overlap, and colored markers indicating trend.
    """
    df = be.get_census_data(full_name, var, True)
    df["Year"] = df["Year"].astype(int)
    df = df.sort_values("Year")

    # Compute percent change relative to previous year
    df["Pct_Change"] = df[var].pct_change() * 100.0

    fig, ax = plt.subplots(figsize=(8, 4))

    # Plot baseline line
    ax.plot(df["Year"], df[var], color="dimgray", marker="o")

    # Overlay colored markers
    for i in range(1, len(df)):
        x = df.iloc[i]["Year"]
        y = df.iloc[i][var]
        pct = df.iloc[i]["Pct_Change"]
        if pct < 0:
            col = NEG_COLOR
        elif pct > 0:
            col = POS_COLOR
        else:
            col = ZERO_COLOR
        ax.scatter([x], [y], color=col, s=80, zorder=5)

    # If missing 2020, connect 2019 → 2021 with dashed line
    if (2019 in df["Year"].values) and (2021 in df["Year"].values):
        v19 = df.loc[df["Year"] == 2019, var].values[0]
        v21 = df.loc[df["Year"] == 2021, var].values[0]
        ax.plot([2019, 2021], [v19, v21], linestyle="--", color="gray")

    # Set x‐ticks at each year and rotate labels
    years = sorted(df["Year"].unique())
    ax.set_xticks(years)
    ax.tick_params(axis="x", labelrotation=45)

    ax.set_xlabel("Year")
    ax.set_title(f"{var} in {full_name}")
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    fig.tight_layout()
    return fig


def get_swarm_dot_size(var: str) -> int:
    """
    Choose dot size in swarm plots depending on variable magnitude / overlap.
    """
    if var == "Total With Public Assistance":
        return 2
    elif var == "Total Population":
        return 3
    else:
        return 4


@st.cache_resource
def get_swarmplot(var: str, year1: int, year2: int, full_name: str):
    """
    Return a seaborn swarm plot of county percent changes,
    coloring negative (red), zero (yellow), positive (blue),
    and highlighting the selected county.
    """
    df = be.get_ranking_df(var, year1, year2, False)

    fig, ax = plt.subplots(figsize=(6, 4))

    df_neg = df[df["Percent Change"] < 0]
    df_zero = df[df["Percent Change"] == 0]
    df_pos = df[df["Percent Change"] > 0]

    size = get_swarm_dot_size(var)

    if not df_neg.empty:
        sns.swarmplot(x=df_neg["Percent Change"], color=NEG_COLOR, size=size, ax=ax)
    if not df_zero.empty:
        sns.swarmplot(x=df_zero["Percent Change"], color=ZERO_COLOR, size=size, ax=ax)
    if not df_pos.empty:
        sns.swarmplot(x=df_pos["Percent Change"], color=POS_COLOR, size=size, ax=ax)

    # Highlight selected county
    df_high = df[df["Full Name"] == full_name]
    if not df_high.empty:
        pc = df_high["Percent Change"].values[0]
        col = NEG_COLOR if pc < 0 else (POS_COLOR if pc > 0 else ZERO_COLOR)
        sns.swarmplot(x=df_high["Percent Change"], color=col, size=size * 2, ax=ax)
        legend_line = plt.Line2D(
            [0], [0],
            marker="o",
            color=col,
            linestyle="None",
            markersize=8,
            label=full_name
        )
        ax.legend(handles=[legend_line])

    ax.set_title(f"Percent Change of {var}\n{year1} to {year2}")
    ax.set_xlabel("Percent Change")
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.1f}"))

    fig.tight_layout()
    return fig
