import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import plotly.express as px

# Introduction to Streamlit
"""
## Used Car Analysis with Streamlit

This app allows users to analyze used car prices across different locations in India. 
It offers interactive features like map visualizations, filtering options based on car brand, model, and year, 
and bar charts displaying average prices.

### Key Features:
- **Map Visualization**: Shows the average car price by location.
- **Price Filtering**: Allows users to filter cars based on brand, model, and year.
- **Top 5 Cities**: Displays the top 5 cities by average car price.

Let's dive into the analysis!
"""

# Function to load data with caching for optimization. 
@st.cache_data(show_spinner="Loading data...") # This is a decorator used for load_data. This helps to cache the output of the function below so it doesnt need to recompute in each run.
def load_data(file):
    df_map = pd.read_csv(file)
    return df_map

# Set the title for the Streamlit app
st.title("Used Car Analysis") 

# Load the data
cars_df = load_data('used_cars_data.csv')

# Data preprocessing: Extracting brand and model information from 'Name' column
cars_df['Brand'] = cars_df.Name.str.split().str.get(0)
cars_df['Model'] = cars_df.Name.str.split().str.get(1) + " " + cars_df.Name.str.split().str.get(2)

# Create a list of unique cities from the 'Location' column
df_cities = cars_df['Location'].unique()

#Since coordinates are not available, we create a separate dataframe for each city with coordinates taken from other sources.
# Define a DataFrame with city coordinates
data_cordinates = {
    'Location': ['Mumbai', 'Pune', 'Chennai', 'Coimbatore', 'Hyderabad', 'Jaipur', 'Kochi', 'Kolkata', 'Delhi', 'Bangalore', 'Ahmedabad'],
    'Latitude': [19.0760, 18.5204, 13.0827, 11.0168, 17.3850, 26.9124, 9.9312, 22.5726, 28.6139, 12.9716, 23.0225],
    'Longitude': [72.8777, 73.8567, 80.2707, 76.9558, 78.4867, 75.7873, 76.2673, 88.3639, 77.2090, 77.5946, 72.5714]
}

df_cordinates = pd.DataFrame(data_cordinates) #Convert the dictionary to dataframe

# Merge the car data with city coordinates
df_cars = pd.merge(cars_df, df_cordinates, on='Location', how='left')

# Aggregate data to get the average price for each city
df_avg_price_by_city = df_cars.groupby(['Location','Latitude','Longitude']).agg({'Price': 'mean'}).reset_index()

# Rename columns for clarity and formatting
df_avg_price_by_city.rename(columns={'Price': 'Average_Price'}, inplace=True)
df_avg_price_by_city['Price_in_thousands'] = round(df_avg_price_by_city['Average_Price'] * 100, 1)
df_avg_price_by_city['Price'] = df_avg_price_by_city['Price_in_thousands'].astype(str) + "K"

#We are using a package scatter_mapbox for interactive map.This is a package where plotly is integrtated with the service mapbox. Mapbox is a platform for mapping and location based services that exposes geospatial data through API.
#A free account has been created with mapbox. The API token is obtained. This token is used in scatter_mapbox provided 
# Your Mapbox token (you will need your own token)
token = "pk.eyJ1Ijoia3NvZGVyaG9sbTIyIiwiYSI6ImNsZjI2djJkOTBmazU0NHBqdzBvdjR2dzYifQ.9GkSN9FUYa86xldpQvCvxA" 

# Create a scatter mapbox plot for average price by city
fig1 = px.scatter_mapbox(df_avg_price_by_city, lat='Latitude', lon='Longitude',
                hover_name='Location', hover_data=['Price'],
                color_discrete_sequence=["fuchsia"], zoom=4) # A layer of scatterplot is created over the map with the use of scatter_mapbox.

# Update marker size and map style
fig1.update_traces(marker={'size': 15})
fig1.update_layout(mapbox_style="mapbox://styles/mapbox/satellite-streets-v12",
                   mapbox_accesstoken=token)
fig1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

# Display the map in Streamlit
st.subheader('Average Car Price by Location in India')
st.plotly_chart(fig1, use_container_width=True) #Display plotly chart

# Filter the data based on user selection for brand, model, and year
st.markdown("### Choose the Brand, Model, and Year to know the average price of the car")
selected_Brand = st.selectbox('Select the Brand of car', cars_df.Brand.unique())
selected_Model = st.selectbox('Select the Model of car', cars_df[cars_df.Brand == selected_Brand].Model.unique())
selected_Year = st.selectbox('Select the Year', cars_df[(cars_df.Brand == selected_Brand) & (cars_df.Model == selected_Model)].Year.unique())

# Filter the DataFrame based on the user's selections
cars_df_filtered = cars_df[(cars_df.Brand == selected_Brand) & (cars_df.Model == selected_Model) & (cars_df.Year == selected_Year)]

# Calculate the average price for the filtered selection
average_price = cars_df_filtered['Price'].mean()

# Display the average price
st.markdown(f'**The average price of the selected car is: {average_price * 100000:.2f} INR**')

# Display a bar chart of average price by city for the selected car
st.subheader('Average Car Price in Selected Cities')
df_avg_price_by_city_new = cars_df_filtered.groupby(['Location']).agg({'Price': 'mean'}).reset_index()

# Rename columns for clarity and formatting
df_avg_price_by_city_new.rename(columns={'Price': 'Average_Price'}, inplace=True)
df_avg_price_by_city_new['Formatted_Price'] = round(df_avg_price_by_city_new['Average_Price'] * 100, 2)
df_avg_price_by_city_new['Price_K'] = df_avg_price_by_city_new['Formatted_Price'].astype(str) + "K"

# Filter the DataFrame to include only the top 5 cities by average price
df_top_5 = df_avg_price_by_city_new.nlargest(5, 'Average_Price')

# Create a bar chart for the top 5 cities by average car price. 
#Altair package  has been used to create the bar chart here. The basic interactions can be done in your chart without any use of the selection interface, using the interactive() shortcut method and the tooltip encoding.

chart = (
    alt.Chart(df_top_5)
    .mark_bar()
    .encode(
        x=alt.X('Formatted_Price:Q', title='Average Price (INR)', axis=alt.Axis(format='~s')),
        y=alt.Y('Location:N', title='Location').sort('-x'),
        color=alt.Color('Formatted_Price:Q', scale=alt.Scale(scheme='viridis'), title='Average Price'),
        tooltip=[
            alt.Tooltip('Location:N', title='Location'),
            alt.Tooltip('Price_K', title='Average Price')
        ]
    )
    .properties(
        title='Top 5 Cities by Average Car Price',
        height=300,
        width=600
    )
    .interactive()
)

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)