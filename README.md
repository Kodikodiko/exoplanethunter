# ExoHunter Pro 🔭

**ExoHunter Pro** is a high-precision observation planner for exoplanet research. It prioritizes data from the **ExoClock project** (ARIEL mission support) and fallbacks to the NASA Exoplanet Archive to provide the most accurate transit predictions for your specific equipment.

## Capabilities

*   **Precision Timing**: Automatically handles **BJD_TDB to UTC** conversions, ensuring transit times are accurate to the minute.
*   **Drift Prediction**: Calculates **Timing Uncertainty (± min)** based on propagated ephemeris errors (T0 and Period uncertainty).
*   **Equipment Suitability**: Filters targets based on your telescope's **aperture (inches)**, using ExoClock's detection thresholds.
*   **Scientific Prioritization**: Highlights "High" and "Alert" priority targets that urgently need follow-up data.
*   **Field-Ready Visualization**: Features a "Nightsight" (Red Mode) to preserve dark adaptation.
*   **Interactive Graphics**: View lightcurves overlaid on sky conditions (twilight/darkness) and moon altitude.

---

## User Guide

### 1. Configuration (Sidebar)
Configure your observatory and equipment in the sidebar:

*   **Observer Location**: Enter **Latitude**, **Longitude**, and **Elevation**. Essential for altitude and twilight calculations.
*   **Equipment**: Use the **Telescope Aperture (inches)** slider. 
    *   *Impact*: The app will hide targets that are mathematically undetectable with your telescope size based on ExoClock SNR models.
*   **Theme**: Choose between **Dark**, **Light**, or **Nightsight (Red)**.
*   **Data Source**: Toggle between **PostgreSQL** (Research DB) and **SQLite** (Portable file).
*   **Update Database**: Fetches fresh ephemerides, uncertainties, and detection thresholds from ExoClock and NASA. **Run this first to populate a new database.**

### 2. Search Parameters
*   **Observation Date & Start Time**: Starting point for calculations.
*   **Window Duration (Hours)**: Up to 336 hours (14 days).
*   **Min Altitude (°)**: Targets must be above this height at mid-transit.
*   **Min Depth (mmag)**: Minimum transit depth (e.g., 10 mmag = 1% flux drop).
*   **Max Magnitude (V)**: The faintest host star your setup can handle.
*   **Priority (ExoClock)**: Filter by scientific urgency (Alert, High, etc.).

### 3. Results & Analysis
Click **"Find Transits"** to generate your schedule.

*   **The Table (Left)**:
    *   **mid_time**: Local Time of transit center. ⚠️ Indicates high uncertainty (>30 min).
    *   **uncertainty**: Predicted error margin (e.g., ± 5 min). Grows over time as ephemerides age!
    *   **altitude**: Elevation at mid-transit.
    *   **depth**: Transit depth in millimagnitudes (mmag).
    *   **duration**: Total transit time in hours.
    *   **Interaction**: **Click a row** to see the detailed lightcurve and sky chart.

*   **The Transit Visualizer (Right)**:
    *   **Lightcurve**: Simulated flux dip.
    *   **Uncertainty Margin**: Shown in the title. Consider starting your sequence early if the uncertainty is high.
    *   **Sky Gradient**: Shows Civil Twilight (Grey), Nautical (Dark Blue), and Night (Black).
    *   **Moon Alt**: White dashed line. High moon illumination can degrade SNR for shallow transits.

---

## Technical Notes
- **Time Standard**: All input ephemerides are treated as **BJD_TDB**. Predicitons are converted to your system's Local Time or UTC.
- **Data Merging**: ExoClock data is treated as the "Gold Standard". NASA data is only used for planets not tracked by the ExoClock/ARIEL network.
- **Uncertainty Formula**: Uses $\sigma_{total} = \sqrt{\sigma_{t0}^2 + (N \times \sigma_{period})^2}$ to account for orbital drift.

---

## Integration (N.I.N.A.)
Click **"Send to N.I.N.A"** to push targets to your imaging software.
*   *Note*: Currently a **Mock Implementation**; verifies API payload construction. Full automation coming soon.

---

## Setup & Installation
... [Rest of installation section remains same] ...