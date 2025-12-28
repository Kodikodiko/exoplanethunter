# ExoHunter Pro 🔭

**ExoHunter Pro** is a specialized observation planner designed for amateur and professional astronomers dedicated to exoplanet research. It combines robust data from the NASA Exoplanet Archive with the operational priorities of the ExoClock project to help you find the most scientifically valuable targets for your location and equipment.

## Capabilities

*   **Smart Planning**: Calculates transit visibility based on your exact location, including constraints for altitude, astronomical twilight, and moon interference.
*   **Scientific Prioritization**: Integrates directly with **ExoClock** to highlight "High" and "Alert" priority targets that urgently need follow-up observations.
*   **Field-Ready Visualization**: Features a "Nightsight" (Red Mode) to preserve dark adaptation while operating at the telescope.
*   **Offline/Hybrid Mode**: Supports running against a live PostgreSQL database or a static SQLite file for portable deployment.
*   **Interactive Visualization**: View detailed lightcurves overlaid on sky conditions (twilight/darkness) and moon altitude.

---

## User Guide

### 1. Configuration (Sidebar)
Before starting, configure your observatory settings in the sidebar (left panel):

*   **Observer Location**: Enter your **Latitude**, **Longitude**, and **Elevation**.
    *   *Default*: N 48.0880°, E 15.7566°, 640m.
    *   *Impact*: These coordinates are used to calculate target altitude, sun position (twilight), and moon position. Accurate entry is crucial for valid results.
*   **Theme**:
    *   **Dark**: Default professional interface.
    *   **Light**: High contrast for daylight planning.
    *   **Nightsight (Red)**: Monochromatic red filter for use in the field to protect night vision.
*   **Data Source**:
    *   **PostgreSQL**: Connects to your local research database (requires `.env` setup).
    *   **SQLite**: Uses the portable `exoplanets.db` file. Useful for cloud hosting or offline use.
*   **N.I.N.A Configuration**: Enter the IP and Port of your N.I.N.A. imaging software (see *Integration* below).
*   **Update Database**: Click this button to fetch the latest planetary data from NASA and priorities from ExoClock. *Run this periodically to keep ephemerides fresh.*

### 2. Search Parameters
The "Search Parameters" section allows you to filter the vast catalog of exoplanets to find targets suitable for your equipment and schedule.

*   **Observation Date & Start Time**: The starting point for the search window.
*   **Window Duration (Hours)**: How far ahead to look.
    *   *Range*: 1 to 336 hours (14 days).
    *   *Default*: 168 hours (1 week).
*   **Min Altitude (°)**: Targets below this altitude at mid-transit will be ignored.
*   **Min Depth (mmag)**: The minimum transit depth required.
    *   *Tip*: Match this to your equipment's sensitivity. 10 mmag = 0.01 mag (1% flux drop).
*   **Max Magnitude (V)**: The faintest host star you can observe.
*   **Priority (ExoClock)**: Filter by scientific urgency.
    *   *Alert*: O-C deviations > 10 mins in last 2 years. **Highest value.**
    *   *High*: Uncertainty > duration or sparse recent data.
    *   *Medium/Normal/Low*: Lower urgency targets.

### 3. Results & Analysis
Click **"Find Transits"** to generate a list of candidates.

*   **The Table (Left)**:
    *   Displays a list of all matching transit events sorted chronologically.
    *   **Columns**:
        *   `mid_time`: Center time of the transit (Local Time).
        *   `altitude`: Elevation of the target at mid-transit.
        *   `depth`: Transit depth in millimagnitudes (mmag).
        *   `duration`: Duration in hours.
        *   `mag_v`: Visual magnitude of the host star.
        *   `moon_ill`: Moon illumination fraction (0.0 - 1.0).
    *   **Interaction**: **Click on any row** to view its detailed chart on the right.
    *   **Download**: Use the **"Download Results CSV"** button below the table to save the entire schedule for offline processing.

*   **The Transit Visualizer (Right)**:
    *   Updates dynamically when a table row is selected.
    *   **Lightcurve (Orange/Red Line)**: Shows the simulated dip in flux (brightness) over time.
    *   **Background Gradient**: Represents sky brightness:
        *   **Light Blue/Grey**: Civil Twilight (Too bright for photometry).
        *   **Dark Blue**: Nautical Twilight.
        *   **Black**: Astronomical Night (Ideal conditions).
    *   **Moon Altitude (White Dashed Line)**: Shows the Moon's elevation during the transit. High moon altitude may degrade SNR.

---

## Integration

### N.I.N.A. (Work in Progress)
The application includes a button **"Send to N.I.N.A"** in the detail view.
*   **Current Status**: **Mock Implementation**.
*   **Function**: Currently, clicking this button verifies the API payload construction but **does not** actually communicate with N.I.N.A. yet.
*   **Future Goal**: To push the selected target's coordinates and name directly to N.I.N.A.'s framing assistant or target list via its API.

---

## Setup & Installation

### Windows 10 (Local)

1.  **Prerequisites**:
    *   Python 3.11+ installed.
    *   PostgreSQL database (optional, can use SQLite mode).

2.  **Run**:
    *   Double-click `run.bat`.
    *   The script handles virtual environment creation and dependency installation automatically.

3.  **Database Config**:
    *   If using PostgreSQL, edit the `.env` file created after the first run:
        ```env
        DB_USER=
        DB_PASSWORD=
        DB_HOST=
        DB_PORT=5432
        DB_NAME=
        ```

### Docker (Server/NAS)

For always-on deployment:
```bash
docker-compose up --build -d
```
Access at `http://<server-ip>:8501`.