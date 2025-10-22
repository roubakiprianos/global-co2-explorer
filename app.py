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
DATA_URL = 'https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv'
df = pd.read_csv(DATA_URL)
    
    # Clean data: drop rows missing CO2 emissions and select relevant columns
    df = df.dropna(subset=['co2', 'co2_per_capita', 'year', 'iso_code'])
    df = df[['country', 'year', 'co2', 'co2_per_capita', 'iso_code', 'population', 'gdp', 'co2_per_gdp', 'cumulative_co2', 'coal_co2', 'oil_co2', 'gas_co2', 'share_global_co2']] 
    
    # Filter out global regions (e.g., World, Africa) to keep only individual countries
    regions_to_exclude = ['World', 'Asia', 'Europe', 'North America', 'South America', 'International transport', 'Micronesia (country)']
    df = df[~df['country'].isin(regions_to_exclude)]
    
    return df

data = load_data()

# --- 2. Sidebar Filters ---
with st.sidebar:
    st.header("Visualization Filters")
    with st.expander("❓ Key Definitions & Metrics"):
        st.markdown("""
        **Total Annual CO2 Emissions:**
        The total amount of carbon dioxide (in million tonnes) emitted by a country from burning fossil fuels and cement production in a given year.
        
        **Share of Global CO₂ (%):**
        A country's annual CO₂ emissions expressed as a percentage of the total global CO₂ emissions for that year. This highlights a country's current global responsibility and contribution to the overall problem.

        **CO2 Per Capita:**
        Total CO2 emissions divided by the country's population, showing the average emissions **per person** (in tonnes). This standardizes the data, revealing consumption patterns.

        **GDP (Total):**
        Gross Domestic Product (GDP) is the total monetary value of all the finished goods and services produced within a country's borders in a specific time period. It measures the country's economic size.

        **CO₂ from Coal/Oil/Gas:**
        The amount of CO₂ emissions (in million tonnes) specifically resulting from the consumption of Coal, Oil, or Gas in a given year. These metrics show a country's reliance on specific fossil fuels.


        **Population:**
        The total number of people residing in the country in a given year.
        """)
    st.markdown("---")    
    # New Filter 1: Comparison Mode Toggle
    comparison_mode = st.radio(
        "Select Comparison Mode",
        ('Total Annual CO₂', 'CO₂ Per Capita'),
        horizontal=True
    )
    st.markdown("---") # Add a separator for clarity
    
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
        "CO₂ Per GDP (Carbon Intensity)": "co2_per_gdp",
        "Share of Global CO₂ (%)": "share_global_co2",
    }
    selected_variable_label = st.selectbox(
        "Select Variable for Time-Series Y-Axis",
        options=list(variable_options.keys()),
        index=0 # Default to CO2
    )
    # Get the column name from the label
    selected_variable_column = variable_options[selected_variable_label]

# Set the dynamic variable based on the radio button choice
if comparison_mode == 'Total Annual CO₂':
    map_variable_column = 'co2'
    map_variable_label = 'Total CO₂ (Million Tonnes)'
    map_color_scale = px.colors.sequential.Reds
else:
    map_variable_column = 'co2_per_capita' # This column exists in the CSV
    map_variable_label = 'CO₂ Per Capita (Tonnes)'
    map_color_scale = px.colors.sequential.Plasma # Use a different color scale for visual distinction
    
# --- 3. Apply Filters ---
# Filter data for the map based on the selected year
map_data = data[data['year'] == selected_year]
# Filter data for the line chart based on selected countries
line_chart_data = data[data['country'].isin(selected_countries)]


# --- 4. Visualizations ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Global {map_variable_label} in {selected_year}")
    
    if not map_data.empty:
        # Create a Choropleth Map (Geospatial Visualization)
        fig_map = px.choropleth(
            map_data,
            locations="iso_code",
            color=map_variable_column,       # 2. Use the dynamic column
            hover_name="country",
            color_continuous_scale=map_color_scale, # 3. Use the dynamic color scale
            title=map_variable_label,
        )
        # ... (rest of the map code remains the same)
        st.plotly_chart(fig_map, use_container_width=True)


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

# --- 5. Fossil Fuel Breakdown Visualization ---
st.markdown("---")
st.subheader("Fossil Fuel CO₂ Breakdown Over Time for Selected Countries")

# Data preparation: select only the required columns and melt the DataFrame for Plotly
melted_data = line_chart_data.melt(
    id_vars=['country', 'year'],
    value_vars=['coal_co2', 'oil_co2', 'gas_co2'],
    var_name='Fuel Type',
    value_name='CO2 Emissions (Million Tonnes)'
)

if not melted_data.empty:
    # Create the Stacked Bar Chart
    fig_bar = px.bar(
        melted_data,
        x='year',
        y='CO2 Emissions (Million Tonnes)',
        color='Fuel Type',
        facet_col='country', # Create separate charts for each selected country
        facet_col_wrap=3,    # Wrap charts after every 3 countries
        title="Annual CO₂ Emissions by Fossil Fuel Source",
        labels={
            'CO2 Emissions (Million Tonnes)': 'CO₂ (Million Tonnes)',
            'year': 'Year',
            'country': 'Country'
        }
    )
    # Tidy up the chart layout
    fig_bar.update_layout(height=450, margin={"t":50, "b":0})
    fig_bar.update_yaxes(matches=None) # Allow y-axes to scale independently for comparison

    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.warning("Select countries in the sidebar to view the fossil fuel breakdown.")

# Final caption remains at the bottom
st.markdown("---")

st.caption(f"**Developed by Rouba Kiprianos.** | Data source: Our World in Data (OWID). Showing data from {min_year} to {max_year}.")
