# app.py - Global CO2 Emissions Dashboard

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Global CO₂ Emissions Explorer 📈🌎")
st.markdown("Visualize annual CO₂ emissions data (in million tonnes) by country and year.")

# --- 1. Load Data ---
# Uses caching to load the large dataset only once
@st.cache_data
def load_data():
    # Load the CSV you downloaded to your project folder
    df = pd.read_csv('owid-co2-data.csv')
    
    # Clean data: drop rows missing CO2 emissions and select relevant columns
    df = df.dropna(subset=['co2', 'year', 'iso_code'])
    df = df[['country', 'year', 'co2', 'iso_code', 'population', 'gdp']]
    
    # Filter out global regions (e.g., World, Africa) to keep only individual countries
    regions_to_exclude = ['World', 'Asia', 'Europe', 'North America', 'South America', 'International transport', 'Micronesia (country)']
    df = df[~df['country'].isin(regions_to_exclude)]
    
    return df

data = load_data()

# --- 2. Sidebar Filters ---
with st.sidebar:
    st.header("Visualization Filters")

    # Filter 1: Year Slider
    min_year = int(data['year'].min())
    max_year = int(data['year'].max())
    
    selected_year = st.slider(
        "Select Year for Map",
        min_value=min_year,
        max_value=max_year,
        value=max_year, # Default to the latest year
        step=1
    )

    # Filter 2: Select a Country (for the Line Chart)
    country_list = sorted(data['country'].unique())
    selected_countries = st.multiselect(
        "Select Countries for Time-Series Chart",
        options=country_list,
        default=['United States', 'China', 'India']
    )
    # Filter 3: Select Y-Axis Variable for Chart
variable_options = {
    "Annual CO₂ Emissions (Million Tonnes)": "co2",
    "Population (Total)": "population",
    "GDP (Total)": "gdp",
}
selected_variable_label = st.selectbox(
    "Select Variable for Time-Series Y-Axis",
    options=list(variable_options.keys()),
    index=0 # Default to CO2
)
# Get the column name from the label
selected_variable_column = variable_options[selected_variable_label]

# --- 3. Apply Filters ---
# Filter data for the map based on the selected year
map_data = data[data['year'] == selected_year]
# Filter data for the line chart based on selected countries
line_chart_data = data[data['country'].isin(selected_countries)]

# --- 4. Visualizations ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Global CO₂ Emissions in {selected_year}")
    
    if not map_data.empty:
        # Create a Choropleth Map (Geospatial Visualization)
        fig_map = px.choropleth(
            map_data,
            locations="iso_code",           # Use the ISO country code for mapping
            color="co2",                    # Color based on CO2 emissions
            hover_name="country",           # Show country name on hover
            color_continuous_scale=px.colors.sequential.Reds, # Use a nice red color scale
            title="Emissions (Million Tonnes)",
        )
        # Set map layout to focus on the world
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(height=450, margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning(f"No CO₂ data available for the year {selected_year}.")


with col2:
    st.subheader(f"{selected_variable_label} Over Time")
    
    if not line_chart_data.empty:
        # Create a Line Chart (Time-Series Visualization)
        fig_line = px.line(
            line_chart_data,
            x='year',               # X-axis is the year
            y=selected_variable_column,  # Use the selected column name
            color='country',        # Use a different color for each country
            title=f'{selected_variable_label} Trend',
    labels={
        selected_variable_column: selected_variable_label, # Use the full label for the axis
        'year': 'Year'
    }
)
        fig_line.update_layout(height=450, margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Select one or more countries in the sidebar to view the time-series trend.")

st.markdown("---")
st.caption(f"Data source: Our World in Data (OWID). Showing data from {min_year} to {max_year}.")
