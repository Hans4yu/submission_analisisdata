import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from babel.numbers import format_currency
import geopandas as gpd
from shapely.geometry import Point


sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_approved_at').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    # Since 'quantity_x' and 'product_name' are not in the dataset, group by 'name_product' and sum 'order_item_id' as a proxy for quantity
    sum_order_items_df = df.groupby("name_product").order_item_id.sum().sort_values(ascending=False).reset_index()
    sum_order_items_df.rename(columns={"order_item_id": "quantity"}, inplace=True)
    return sum_order_items_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return bystate_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_approved_at": "max",  # Latest order date
        "order_id": "nunique",       # Frequency
        "payment_value": "sum"       # Monetary
    })
    rfm_df.columns = ["customer_id", "order_approved_at", "frequency", "monetary"]
    
    rfm_df["order_approved_at"] = rfm_df["order_approved_at"].dt.date
    recent_date = df["order_approved_at"].dt.date.max()  # Use order_approved_at since order_date is not available
    rfm_df["recency"] = rfm_df["order_approved_at"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("order_approved_at", axis=1, inplace=True)
    
    return rfm_df

# Load dataset
all_df = pd.read_csv('ordered_df.csv')
satisfaction_df = pd.read_csv('satisfaction_df.csv')

# Convert order_approved_at to datetime
all_df['order_approved_at'] = pd.to_datetime(all_df['order_approved_at'])
all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(inplace=True, drop=True)

# Get min and max dates
min_date = all_df["order_approved_at"].min()
max_date = all_df["order_approved_at"].max()

# Sidebar for date range input
with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter data based on date range
main_df = all_df[(all_df["order_approved_at"] >= pd.to_datetime(start_date)) & 
                 (all_df["order_approved_at"] <= pd.to_datetime(end_date))]

# Create dataframes for visualization
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# Dashboard title
st.header('Dicoding E-Commerce Public Dataset :sparkles:')

# Daily Orders section
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO')
    st.metric("Total Revenue", value=total_revenue)

# Plot daily orders
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_approved_at"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

# Best & Worst Performing Product section
st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

# Best performing products
sns.barplot(x="quantity", y="name_product", data=sum_order_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

# Worst performing products
sns.barplot(x="quantity", y="name_product", data=sum_order_items_df.sort_values(by="quantity", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Extended color palette
colors = ["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", 
          "#f95d6a", "#ff7c43", "#ffa600", "#00b4d8", "#0077b6"]

# 1. Review Scores by City
st.header("Review Scores by City")

city_review_sum = satisfaction_df.groupby('seller_city')['review_score'].sum()

top_10_cities = city_review_sum.sort_values(ascending=False).head(10)
bottom_10_cities = city_review_sum.sort_values(ascending=True).head(10)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

sns.barplot(x=top_10_cities.values, y=top_10_cities.index, orient="h", palette=colors, ax=axes[0])
axes[0].set_xlabel("Total Review Score")
axes[0].set_ylabel("Cities")
axes[0].set_title("Top 10 Cities (Highest Scores)")

sns.barplot(x=bottom_10_cities.values, y=bottom_10_cities.index, orient="h", palette=colors, ax=axes[1])
axes[1].set_xlabel("Total Review Score")
axes[1].set_ylabel("Cities")
axes[1].set_title("Top 10 Cities (Lowest Scores)")

plt.tight_layout()
st.pyplot(fig)

# 2. Delivery Time Analysis
st.header("Delivery Time Analysis")

average_delivery_time_by_city = satisfaction_df.groupby('seller_city')['time_deliver_tocarrier'].mean()

top_10_highest = average_delivery_time_by_city.sort_values(ascending=False).head(10)
top_10_lowest = average_delivery_time_by_city.sort_values(ascending=True).head(10)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

sns.barplot(x=top_10_highest.values, y=top_10_highest.index, orient="h", palette=colors, ax=axes[0])
axes[0].set_xlabel("Avg Delivery Time (days)")
axes[0].set_ylabel("Cities")
axes[0].set_title("Top 10 Slowest Cities")

sns.barplot(x=top_10_lowest.values, y=top_10_lowest.index, orient="h", palette=colors, ax=axes[1])
axes[1].set_xlabel("Avg Delivery Time (days)")
axes[1].set_ylabel("Cities")
axes[1].set_title("Top 10 Fastest Cities")

plt.tight_layout()
st.pyplot(fig)

# 3. Late Deliveries Analysis
st.header("Late Deliveries Analysis")

top_10_late = satisfaction_df[satisfaction_df['delivery_status'] == 'Late'] \
                .groupby('seller_city')['delivery_status'].count() \
                .sort_values(ascending=False).head(10)

bottom_10_late = satisfaction_df[satisfaction_df['delivery_status'] == 'Late'] \
                   .groupby('seller_city')['delivery_status'].count() \
                   .sort_values(ascending=True).head(10)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

axes[0].bar(top_10_late.index, top_10_late.values, color=colors)
axes[0].set_title('Cities with Most Late Deliveries')
axes[0].set_xlabel('City')
axes[0].set_ylabel('Count')
axes[0].tick_params(axis='x', rotation=45)

axes[1].bar(bottom_10_late.index, bottom_10_late.values, color=colors)
axes[1].set_title('Cities with Fewest Late Deliveries')
axes[1].set_xlabel('City')
axes[1].set_ylabel('Count')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
st.pyplot(fig)

# 4. On-Time Deliveries Analysis
st.header("On-Time Deliveries Analysis")

top_10_ontime = satisfaction_df[satisfaction_df['delivery_status'] == 'On Time'] \
                  .groupby('seller_city')['delivery_status'].count() \
                  .sort_values(ascending=False).head(10)

bottom_10_ontime = satisfaction_df[satisfaction_df['delivery_status'] == 'On Time'] \
                     .groupby('seller_city')['delivery_status'].count() \
                     .sort_values(ascending=True).head(10)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

axes[0].bar(top_10_ontime.index, top_10_ontime.values, color=colors)
axes[0].set_title('Cities with Most On-Time Deliveries')
axes[0].set_xlabel('City')
axes[0].set_ylabel('Count')
axes[0].tick_params(axis='x', rotation=45)

axes[1].bar(bottom_10_ontime.index, bottom_10_ontime.values, color=colors)
axes[1].set_title('Cities with Least On-Time Deliveries')
axes[1].set_xlabel('City')
axes[1].set_ylabel('Count')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
st.pyplot(fig)

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Set up the color palette
colors = ["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", 
          "#f95d6a", "#ff7c43", "#ffa600", "#00b4d8", "#0077b6"]

# Review Score Analysis
st.header("Review Scores by Seller City")

# Check if 'review_score' exists in the dataframe
if 'review_score' in satisfaction_df.columns:
    # Group by city and sum review scores
    city_review_sum = satisfaction_df.groupby('seller_city')['review_score'].sum()
    
    # Get top and bottom cities
    top_10_cities = city_review_sum.sort_values(ascending=False).head(10)
    bottom_10_cities = city_review_sum.sort_values(ascending=True).head(10)
    
    # Create the plot
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot highest review scores
    sns.barplot(x=top_10_cities.values, y=top_10_cities.index, 
                orient="h", palette=colors, ax=axes[0])
    axes[0].set_xlabel("Total Review Score")
    axes[0].set_ylabel("Cities")
    axes[0].set_title("Top 10 Cities (Highest Scores)")
    
    # Plot lowest review scores
    sns.barplot(x=bottom_10_cities.values, y=bottom_10_cities.index, 
                orient="h", palette=colors, ax=axes[1])
    axes[1].set_xlabel("Total Review Score")
    axes[1].set_ylabel("Cities")
    axes[1].set_title("Top 10 Cities (Lowest Scores)")
    
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.warning("No 'review_score' column found in the dataset. Cannot display review analysis.")

st.markdown(
    """
    Pertanyaan 1. Bagaimana hasil segmentasi kepuasan pelanggan berdasarkan ulasan terhadap e-commerce, khususnya dalam kaitannya dengan kota penjual dan rating tertinggi, waktu pemesanan, status pengiriman, serta rating terbanyak?
    """
)

with st.expander("See explanation"):
    st.write(
        """
**Pertanyaan 1. Bagaimana hasil segmentasi kepuasan pelanggan berdasarkan ulasan terhadap e-commerce, khususnya dalam kaitannya dengan kota penjual dan rating tertinggi, waktu pemesanan, status pengiriman, serta rating terbanyak?**

1. Kota Penjual dengan Rating dan Kepuasan Tinggi
  Kota dengan pengiriman tepat waktu terbanyak:

  Sao Paulo (24.5K), Ibitinga (7K), Santo Andre (2.8K)

  Kota dengan pengiriman paling cepat:

  Sao Sebastiao da Grama/SP, Bom Jardim, Juazeiro do Norte (semua di bawah 0.4 hari)

  Kota dengan sedikit keterlambatan:

  Abadia de Goias, Afonso Claudio, Anapolis, dll (1 keterlambatan)

2. Kota Penjual dengan Rating dan Kepuasan Rendah
  Kota dengan keterlambatan terbanyak:

  Sao Paulo (2.4K), Ibitinga (620), Itaquaquecetuba (490)

  Kota dengan waktu pengiriman paling lama:

  Porto Ferreira (30 hari), Santo Antonio da Patrulha (27 hari), Sao Paulo SP (19 hari)

3. Status Pengiriman
  Kota dengan keterlambatan tinggi juga masuk daftar pengiriman tepat waktu → indikasi volume transaksi besar (cth: Sao Paulo).

  Kota dengan pengiriman tepat waktu dan cepat cenderung kecil dan jarang keterlambatan → lebih konsisten.

        """
    )

# 1. Top/Bottom cities by order count
st.header("Order Distribution by City")

seller_city_counts = all_df.groupby('seller_city')['order_item_id'].count()
top_10_cities = seller_city_counts.sort_values(ascending=False).head(10)
bottom_10_cities = seller_city_counts.sort_values(ascending=True).head(10)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Plot the top 10 cities
sns.barplot(x=top_10_cities.index, y=top_10_cities.values, palette=colors, ax=axes[0])
axes[0].set_xlabel("Seller City")
axes[0].set_ylabel("Number of Orders")
axes[0].set_title("Top 10 Cities with Most Orders")
axes[0].tick_params(axis='x', rotation=45)

# Plot the bottom 10 cities
sns.barplot(x=bottom_10_cities.index, y=bottom_10_cities.values, palette=colors, ax=axes[1])
axes[1].set_xlabel("Seller City")
axes[1].set_ylabel("Number of Orders")
axes[1].set_title("Bottom 10 Cities with Fewest Orders")
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
st.pyplot(fig)  # Use st.pyplot() instead of plt.show()

st.markdown(
    """
    Pertanyaan 2: Bagaimana distribusi kota penjual (seller_city), Kota mana yang memiliki jumlah penjualan terbanyak dan terdikit?
    """
)

with st.expander("See explanation"):
    st.write(
        """
**Pertanyaan 2: Bagaimana distribusi kota penjual (seller_city), Kota mana yang memiliki jumlah penjualan terbanyak dan terdikit?**

1. Kota Penjual dengan Jumlah Penjualan Terbanyak
  Kota dengan jumlah order tertinggi:

  Sao Paulo (±18.000 pesanan)

  Rio de Janeiro (±8.000 pesanan)

  Belo Horizonte (±3.000 pesanan)

  Brasilia (±2.400 pesanan)

  Curitiba (±1.800 pesanan)

  Campinas, Porto Alegre, Salvador, Guarulhos, Sao Bernardo do Campo (semua di kisaran 1.200–1.600 pesanan)

2. Kota Penjual dengan Jumlah Penjualan Paling Sedikit
  Kota dengan hanya 1 pesanan:

  Agisse, Virginia, Viseu, Vista Alegre, Aguas Claras, Abadiania, Abrantes, Cordeiros, Coreau, Coronel Domingos Soares
        """
    )

# 2. Top/Bottom products by sales volume
st.header("Product Sales Distribution")

top_10_products = all_df.groupby('name_product')['order_item_id'].count().sort_values(ascending=False).head(10)
bottom_10_products = all_df.groupby('name_product')['order_item_id'].count().sort_values(ascending=True).head(10)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Plot the top 10 products
sns.barplot(x=top_10_products.values, y=top_10_products.index, palette=colors, ax=axes[0])
axes[0].set_xlabel("Number of Orders")
axes[0].set_ylabel("Product Name")
axes[0].set_title("Top 10 Products with Most Orders")

# Plot the bottom 10 products
sns.barplot(x=bottom_10_products.values, y=bottom_10_products.index, palette=colors, ax=axes[1])
axes[1].set_xlabel("Number of Orders")
axes[1].set_ylabel("Product Name")
axes[1].set_title("Bottom 10 Products with Fewest Orders")

plt.tight_layout()
st.pyplot(fig)

st.markdown(
    """
    Pertanyaan 3: Apa saja produk/barang yang memiliki penjualan tertinggi dan terendah?    
    """
)

with st.expander("See explanation"):
    st.write(
        """
**Pertanyaan 3: Apa saja produk/barang yang memiliki penjualan tertinggi dan terendah?**

1. Produk dengan Penjualan Tertinggi
Kategori dengan jumlah order terbanyak:

  bed_bath_table (±11.500 pesanan)

  health_beauty (±9.800 pesanan)

  sports_leisure (±8.600 pesanan)

  furniture_decor (±8.500 pesanan)

  computers_accessories (±7.800 pesanan)

  housewares (±7.300 pesanan)

  watches_gifts (±6.100 pesanan)

  telephony & garden_tools (±4.700 pesanan)

  auto (±4.500 pesanan)

2. Produk dengan Penjualan Terendah
Kategori dengan jumlah order paling sedikit:

  security_and_services (±2 pesanan)

  fashion_childrens_clothes (±7 pesanan)

  cds_dvds_musicals (±14 pesanan)

  la_cuisine (±16 pesanan)

  arts_and_craftsmanship (±24 pesanan)

  fashion_sport (±29 pesanan)

  home_comfort_2 (±31 pesanan)

  flowers (±34 pesanan)

  diapers_and_hygiene (±38 pesanan)

  music (±40 pesanan)        
  """
    )

# 3. Customer distribution by city
st.header("Customer Distribution by City")

customer_city_counts = all_df.groupby('customer_city')['customer_id'].nunique()
top_10_customer_cities = customer_city_counts.sort_values(ascending=False).head(10)
bottom_10_customer_cities = customer_city_counts.sort_values(ascending=True).head(10)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Plot the top 10 customer cities
sns.barplot(x=top_10_customer_cities.values, y=top_10_customer_cities.index, palette=colors, ax=axes[0])
axes[0].set_xlabel("Number of Unique Customers")
axes[0].set_ylabel("Customer City")
axes[0].set_title("Top 10 Cities with Most Customers")

# Plot the bottom 10 customer cities
sns.barplot(x=bottom_10_customer_cities.values, y=bottom_10_customer_cities.index, palette=colors, ax=axes[1])
axes[1].set_xlabel("Number of Unique Customers")
axes[1].set_ylabel("Customer City")
axes[1].set_title("Bottom 10 Cities with Fewest Customers")

plt.tight_layout()
st.pyplot(fig)

# 4. Customer distribution by state
st.header("Customer Distribution by State")

customer_state_counts = all_df.groupby('customer_state')['customer_id'].nunique().sort_values(ascending=False)

fig = plt.figure(figsize=(10, 6))
sns.barplot(x=customer_state_counts.values, y=customer_state_counts.index, palette=colors)
plt.xlabel("Number of Unique Customers")
plt.ylabel("Customer State")
plt.title("Distribution of Customers by State")

st.pyplot(fig)

st.markdown(
    """
    Pertanyaan 4: Bagaimana distribusi kota pelanggan (customer_city) dan negara bagian pelanggan (customer_state)? Wilayah mana yang memiliki jumlah pelanggan terbanyak?    """
)

with st.expander("See explanation"):
    st.write(
        """
**Pertanyaan 4: Bagaimana distribusi kota pelanggan (customer_city) dan negara bagian pelanggan (customer_state)? Wilayah mana yang memiliki jumlah pelanggan terbanyak?**

1. Kota dengan Jumlah Pelanggan Terbanyak (Top 10):

  Sao Paulo (~17.000 pelanggan)

  Rio de Janeiro

  Belo Horizonte

2. Kota dengan Jumlah Pelanggan Paling Sedikit (Bottom 10):
  Semua kota ini memiliki hanya 1 pelanggan:

  Agisse, Virginia, Viseu, Vista Alegre, Aguas Claras, Abadiania, Abrantes, Cordeiros, Coreau, Coronel Domingos Soares

3. Distribusi Berdasarkan Negara Bagian (customer_state):

  SP (São Paulo) adalah negara bagian dengan jumlah pelanggan terbanyak (~48.000)

  Diikuti oleh RJ (Rio de Janeiro) dan MG (Minas Gerais)

  Negara bagian dengan jumlah pelanggan paling sedikit termasuk RR, AP, AC, AM, dan RO"""
    )

# 5. Payment analysis
st.header("Payment Analysis")

# Payment types distribution
st.subheader("Payment Type Distribution")
payment_type_counts = all_df.groupby('payment_type')['order_id'].count().sort_values(ascending=False)

fig = plt.figure(figsize=(10, 6))
sns.barplot(x=payment_type_counts.index, y=payment_type_counts.values, palette=colors)
plt.xlabel("Payment Type")
plt.ylabel("Number of Orders")

st.pyplot(fig)

# Average payment installments by city
st.subheader("Average Payment Installments by City")
avg_installments = all_df.groupby('seller_city')['payment_installments'].mean().sort_values(ascending=False)
top_10_installments = avg_installments.head(10)

fig = plt.figure(figsize=(10, 6))
sns.barplot(x=top_10_installments.values, y=top_10_installments.index, palette=colors)
plt.xlabel("Average Payment Installments")
plt.ylabel("Seller City")
plt.title("Top 10 Cities with Highest Average Payment Installments")

st.pyplot(fig)

# RFM Analysis
st.subheader("Best Customer Based on RFM Parameters")

# Calculate RFM metrics
# For this example, I'll use the latest date in your data as reference point
current_date = pd.to_datetime(all_df['order_approved_at']).max()

rfm_df = all_df.groupby('customer_id').agg({
    'order_approved_at': lambda x: (current_date - pd.to_datetime(x).max()).days,  # Recency
    'order_id': 'nunique',  # Frequency
    'payment_value': 'sum'  # Monetary
}).reset_index()

rfm_df.columns = ['customer_id', 'recency', 'frequency', 'monetary']

# Display average metrics
col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = round(rfm_df.monetary.mean(), 2)
    st.metric("Average Monetary", value=f"${avg_monetary:,.2f}")

# Create visualizations
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 10))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

# Recency plot (lowest values are better)
sns.barplot(y="recency", x="customer_id", 
            data=rfm_df.sort_values(by="recency", ascending=False).head(5), 
            palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Customer ID", fontsize=12)
ax[0].set_title("Top Customers by Recency (days)", loc="center", fontsize=15)
ax[0].tick_params(axis='y', labelsize=12)
ax[0].tick_params(axis='x', labelsize=12, rotation=45)

# Frequency plot (highest values are better)
sns.barplot(y="frequency", x="customer_id", 
            data=rfm_df.sort_values(by="frequency", ascending=False).head(5), 
            palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Customer ID", fontsize=12)
ax[1].set_title("Top Customers by Frequency", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=12)
ax[1].tick_params(axis='x', labelsize=12, rotation=45)

# Monetary plot (highest values are better)
sns.barplot(y="monetary", x="customer_id", 
            data=rfm_df.sort_values(by="monetary", ascending=False).head(5), 
            palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("Customer ID", fontsize=12)
ax[2].set_title("Top Customers by Monetary Value", loc="center", fontsize=15)
ax[2].tick_params(axis='y', labelsize=12)
ax[2].tick_params(axis='x', labelsize=12, rotation=45)

plt.tight_layout()
st.pyplot(fig)

st.caption('Copyright © Your Company 2023')


# Set up the color palette
colors = [
    '#003f5c', '#2f4b7c', '#665191', '#a05195',
    '#d45087', '#f95d6a', '#ff7c43', '#ffa600'
]

st.header("Geospatial Customer Distribution in Brazil")

# Create a copy of your dataframe
geo_df = pd.read_csv('geo_result_df.csv')

try:
    # Create geometry from coordinates
    geometry = [Point(xy) for xy in zip(geo_df['geolocation_lng'], geo_df['geolocation_lat'])]
    geo_df = gpd.GeoDataFrame(geo_df, geometry=geometry, crs="EPSG:4326")
except KeyError:
    st.warning("""
    Geospatial visualization requires latitude/longitude data. 
    Your dataset needs 'geolocation_lat' and 'geolocation_lng' columns.
    """)
    st.stop()

# Get Brazil map outline
try:
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    brazil = world[world['name'] == 'Brazil']
except:
    try:
        brazil_url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
        brazil = gpd.read_file(brazil_url)
        brazil = brazil[brazil['ADMIN'] == 'Brazil']
    except:
        st.warning("Couldn't download Brazil map, using approximate boundaries")
        # Approximate Brazil bounding box
        xmin, ymin, xmax, ymax = -73.9922, -33.7683, -34.7299, 5.2713
        from shapely.geometry import box
        brazil = gpd.GeoDataFrame(geometry=[box(xmin, ymin, xmax, ymax)], crs="EPSG:4326")

# Create color groups based on customer state
geo_df['color_group'] = pd.factorize(geo_df['customer_state'])[0] % len(colors)
color_mapping = {i: colors[i] for i in range(len(colors))}

# Create the plot
fig, ax = plt.subplots(figsize=(12, 15))

# Plot Brazil outline
brazil.boundary.plot(ax=ax, linewidth=1, color='white')

# Plot customer points
for i, color in color_mapping.items():
    subset = geo_df[geo_df['color_group'] == i]
    if not subset.empty:
        subset.plot(ax=ax, color=color, markersize=15, alpha=0.7, label=subset['customer_state'].iloc[0])

# Set black background
ax.set_facecolor('black')
fig.patch.set_facecolor('black')

# Remove axis
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

# Set view to data bounds with padding
if not geo_df.empty:
    min_x, min_y, max_x, max_y = geo_df.total_bounds
    padding = 2
    ax.set_xlim([min_x-padding, max_x+padding])
    ax.set_ylim([min_y-padding, max_y+padding])

# Add legend
ax.legend(title='Customer States', facecolor='black', labelcolor='white')

# Add title
plt.title('Customer Distribution in Brazil', color='white', fontsize=16)

# Display in Streamlit
st.pyplot(fig)

def fig_to_bytes(fig):
    """Convert matplotlib figure to bytes for download"""
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor='black', bbox_inches='tight', dpi=300)
    buf.seek(0)
    return buf

# Optional: Download button
st.download_button(
    label="Download Visualization",
    data=fig_to_bytes(fig),
    file_name="brazil_customer_distribution.png",
    mime="image/png"
)

