# ==========================================================
# SOLAR PV DATA ANALYSIS AND ENERGY ESTIMATION
# Location: Lumle, Nepal
# ==========================================================

import pandas as pd
import matplotlib.pyplot as plt
import pvlib


# ==========================================================
# 1. LOAD AND UNDERSTAND THE DATA
# ==========================================================

df = pd.read_csv(
    "data/solar-measurements_nepal_lumle_wb-esmap_qc.csv"
)

# Convert time from text to datetime
df['time'] = pd.to_datetime(df['time'])

# Set time as index
df = df.set_index('time')


print("\n===== DATASET INFORMATION =====")

print("\nFirst 5 rows:")
print(df.head())

print("\nColumn names:")
print(df.columns)

print("\nDataset shape:")
print(df.shape)

print("\nDataset information:")
print(df.info())

print("\nMissing values:")
print(df.isnull().sum())


# ==========================================================
# 2. CONVERT MINUTE DATA TO HOURLY DATA
# ==========================================================

hourly = df.resample('1h').mean(numeric_only=True)


# ==========================================================
# 3. RELATIONSHIPS BETWEEN GHI AND WEATHER PARAMETERS
# ==========================================================

fig, axes = plt.subplots(
    2, 2,
    figsize=(14, 11)
)


# GHI vs Air Temperature
axes[0, 0].scatter(
    hourly['air_temperature'],
    hourly['ghi'],
    alpha=0.3
)

axes[0, 0].set_xlabel('Air Temperature (°C)')
axes[0, 0].set_ylabel('GHI (W/m²)')
axes[0, 0].set_title('GHI vs Air Temperature')
axes[0, 0].grid(True)


# GHI vs Relative Humidity
axes[0, 1].scatter(
    hourly['relative_humidity'],
    hourly['ghi'],
    alpha=0.3
)

axes[0, 1].set_xlabel('Relative Humidity (%)')
axes[0, 1].set_ylabel('GHI (W/m²)')
axes[0, 1].set_title('GHI vs Relative Humidity')
axes[0, 1].grid(True)


# GHI vs Wind Speed
axes[1, 0].scatter(
    hourly['wind_speed'],
    hourly['ghi'],
    alpha=0.3
)

axes[1, 0].set_xlabel('Wind Speed (m/s)')
axes[1, 0].set_ylabel('GHI (W/m²)')
axes[1, 0].set_title('GHI vs Wind Speed')
axes[1, 0].grid(True)


# GHI vs Rain
axes[1, 1].scatter(
    hourly['rain'],
    hourly['ghi'],
    alpha=0.3
)

axes[1, 1].set_xlabel('Rain')
axes[1, 1].set_ylabel('GHI (W/m²)')
axes[1, 1].set_title('GHI vs Rain')
axes[1, 1].grid(True)


plt.tight_layout(pad=3.0)
plt.savefig(
    'ghi.weather_relationships.png',
    dpi=300
)
plt.show()


# ==========================================================
# 4. CORRELATION ANALYSIS
# ==========================================================

correlation = hourly[
    [
        'ghi',
        'dni',
        'dhi',
        'air_temperature',
        'relative_humidity',
        'wind_speed',
        'rain'
    ]
].corr()

print("\n===== CORRELATION MATRIX =====")
print(correlation)


# ==========================================================
# 5. MONTHLY SOLAR IRRADIATION — 2019
# ==========================================================

# Select only 2019
df_2019 = df[
    (df.index >= '2019-01-01') &
    (df.index < '2020-01-01')
].copy()

# Create date column
df_2019['date'] = df_2019.index.date

# Calculate daily GHI irradiation
daily_ghi_2019 = (
    df_2019.groupby('date')['ghi'].sum() / 60
)

# Convert index to datetime
daily_ghi_2019.index = pd.to_datetime(
    daily_ghi_2019.index
)

# Average daily irradiation for each month
monthly_irradiation_2019 = (
    daily_ghi_2019
    .groupby(daily_ghi_2019.index.month)
    .mean()
)


# Plot monthly irradiation
plt.figure(figsize=(10, 5))

plt.plot(
    monthly_irradiation_2019.index,
    monthly_irradiation_2019.values,
    marker='o'
)

plt.xlabel('Month')
plt.ylabel(
    'Average Daily Irradiation (Wh/m²/day)'
)

plt.title(
    'Monthly Solar Irradiation at Lumle, Nepal — 2019'
)

plt.xticks(
    range(1, 13),
    [
        'Jan', 'Feb', 'Mar', 'Apr',
        'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec'
    ]
)

plt.grid(True)
plt.tight_layout()
plt.savefig(
    'results/monthly_irradiation_2019.png',
    dpi=300
)
plt.show()
# ==========================================================
# 6. SEASONAL VARIATION
# ==========================================================

# Make a copy of the daily 2019 GHI data
seasonal_data = daily_ghi_2019.copy()

# Create a month column
seasonal_data = seasonal_data.to_frame(name='daily_ghi')

seasonal_data['month'] = seasonal_data.index.month


# Function to assign seasons
def get_season(month):

    if month in [12, 1, 2]:
        return 'Winter'

    elif month in [3, 4, 5]:
        return 'Spring'

    elif month in [6, 7, 8]:
        return 'Summer'

    else:
        return 'Autumn'


# Create season column
seasonal_data['season'] = (
    seasonal_data['month'].apply(get_season)
)


# Calculate average daily irradiation for each season
seasonal_irradiation = (
    seasonal_data
    .groupby('season')['daily_ghi']
    .mean()
)


# Put seasons in correct order
season_order = [
    'Winter',
    'Spring',
    'Summer',
    'Autumn'
]

seasonal_irradiation = (
    seasonal_irradiation
    .reindex(season_order)
)


# Print results
print("\n===== SEASONAL SOLAR IRRADIATION =====")
print(seasonal_irradiation)


# Plot seasonal variation
plt.figure(figsize=(9, 5))

plt.bar(
    seasonal_irradiation.index,
    seasonal_irradiation.values
)

plt.xlabel('Season')

plt.ylabel(
    'Average Daily Irradiation (Wh/m²/day)'
)

plt.title(
    'Seasonal Variation of Solar Irradiation at Lumle — 2019'
)

plt.grid(axis='y')

plt.tight_layout()
plt.savefig(
    'results/seasonal_variation.png',
    dpi=300
)
plt.show()

# ==========================================================
# 7. PV SYSTEM PARAMETERS
# ==========================================================

latitude = 28.2965
longitude = 83.8179

timezone = 'Asia/Kathmandu'

# Initial/reference tilt
tilt = 30

# South-facing panel in pvlib convention
surface_azimuth = 180

# Reference PV system
pv_size = 1       # kWp

# Assumed performance ratio
PR = 0.80

# Ground reflectance
albedo = 0.2


# ==========================================================
# 8. CALCULATE SOLAR POSITION
# ==========================================================

location = pvlib.location.Location(
    latitude,
    longitude,
    tz=timezone
)

solar_position = location.get_solarposition(
    hourly.index
)


# ==========================================================
# 9. CALCULATE POA IRRADIANCE FOR 30° TILT
# ==========================================================

poa = pvlib.irradiance.get_total_irradiance(

    surface_tilt=tilt,

    surface_azimuth=surface_azimuth,

    solar_zenith=solar_position[
        'apparent_zenith'
    ],

    solar_azimuth=solar_position[
        'azimuth'
    ],

    dni=hourly['dni'],

    ghi=hourly['ghi'],

    dhi=hourly['dhi'],

    albedo=albedo
)


# Add POA to hourly data
hourly['poa_global'] = poa['poa_global']


# ==========================================================
# 10. ESTIMATE PV ENERGY FOR 30° TILT
# ==========================================================

hourly['pv_energy'] = (

    hourly['poa_global']
    / 1000
    * pv_size
    * PR

)


# ==========================================================
# 11. DAILY PV ENERGY
# ==========================================================

daily_pv = (
    hourly['pv_energy']
    .resample('1D')
    .sum()
)


# ==========================================================
# 12. MONTHLY PV ENERGY
# ==========================================================

monthly_pv = (
    daily_pv
    .resample('ME')
    .sum()
)


# ==========================================================
# 13. YEARLY PV ENERGY
# ==========================================================

yearly_pv = (
    daily_pv
    .resample('YE')
    .sum()
)

print("\n===== YEARLY PV ENERGY =====")
print(yearly_pv)


# ==========================================================
# 14. YEARLY PV GENERATION GRAPH
# ==========================================================

plt.figure(figsize=(10, 5))

plt.bar(
    yearly_pv.index.year.astype(str),
    yearly_pv.values
)

plt.xlabel('Year')
plt.ylabel('PV Energy (kWh/year)')

plt.title(
    'Estimated Annual PV Energy Generation\n'
    '1 kWp System at Lumle, Nepal'
)

plt.grid(axis='y')
plt.tight_layout()
plt.savefig(
    'results/yearly_pv_generation.png',
    dpi=300
)
plt.show()


# ==========================================================
# 15. MONTHLY PV GENERATION GRAPH
# ==========================================================

plt.figure(figsize=(14, 5))

plt.plot(
    monthly_pv.index,
    monthly_pv.values,
    marker='o'
)

plt.xlabel('Date')
plt.ylabel('PV Energy (kWh/month)')

plt.title(
    'Estimated Monthly PV Energy Generation\n'
    '1 kWp System at Lumle, Nepal'
)

plt.grid(True)
plt.tight_layout()
plt.savefig(
    'results/monthly_pv_generation.png',
    dpi=300
)
plt.show()


# ==========================================================
# 16. TILT ANGLE OPTIMIZATION
# ==========================================================

# Test different panel tilt angles
tilt_angles = range(0, 61, 5)

annual_energy_by_tilt = {}


# We will use complete year 2019
hourly_2019 = hourly[
    (hourly.index >= '2019-01-01') &
    (hourly.index < '2020-01-01')
].copy()


# Solar position for 2019
solar_position_2019 = location.get_solarposition(
    hourly_2019.index
)


# Calculate PV generation for each tilt angle
for test_tilt in tilt_angles:

    poa_test = pvlib.irradiance.get_total_irradiance(

        surface_tilt=test_tilt,

        surface_azimuth=surface_azimuth,

        solar_zenith=solar_position_2019[
            'apparent_zenith'
        ],

        solar_azimuth=solar_position_2019[
            'azimuth'
        ],

        dni=hourly_2019['dni'],

        ghi=hourly_2019['ghi'],

        dhi=hourly_2019['dhi'],

        albedo=albedo
    )


    # Calculate energy for this tilt
    energy = (
        poa_test['poa_global']
        / 1000
        * pv_size
        * PR
    )


    # Add all energy produced during 2019
    annual_energy_by_tilt[test_tilt] = (
        energy.sum()
    )


# Convert results into a DataFrame
tilt_results = pd.DataFrame(
    {
        'Tilt Angle (degrees)':
            list(annual_energy_by_tilt.keys()),

        'Annual PV Energy (kWh)':
            list(annual_energy_by_tilt.values())
    }
)


# Find optimum tilt
optimal_row = tilt_results.loc[
    tilt_results['Annual PV Energy (kWh)'].idxmax()
]


optimal_tilt = optimal_row[
    'Tilt Angle (degrees)'
]

maximum_energy = optimal_row[
    'Annual PV Energy (kWh)'
]


print("\n===== TILT ANGLE OPTIMIZATION =====")

print(
    tilt_results
)

print(
    f"\nOptimal Tilt Angle: "
    f"{optimal_tilt:.0f}°"
)

print(
    f"Maximum Annual PV Energy: "
    f"{maximum_energy:.2f} kWh/year"
)


# Plot tilt optimization
plt.figure(figsize=(10, 5))

plt.plot(
    tilt_results['Tilt Angle (degrees)'],
    tilt_results['Annual PV Energy (kWh)'],
    marker='o'
)

plt.xlabel('PV Panel Tilt Angle (degrees)')
plt.ylabel('Annual PV Energy (kWh/year)')

plt.title(
    'PV Tilt Angle Optimization at Lumle, Nepal — 2019'
)

plt.grid(True)
plt.tight_layout()
plt.savefig(
    'results/tilt_optimization.png',
    dpi=300
)
plt.show()