# =================================================================================
# This script is used to generate a PDF report for a given athlete
# The report will be generated using the data from the GCP BigQuery database
# The PDF report will feature the following:
# Page 1: Athlete Name, Age, Test Date, Overall Spider Chart, and Spider Chart Data
# Page 2: Injury Risk????
# Page 3: Composite Score (for in house athletes in age range)
# =================================================================================

# -- IMPORTANT NOTE ---------------------------------------------------------------
# Currently using a manually pulled CMJ reference data base (old_CMJ_ref.csv)
#       This is because the new CMJ reference data is not yet available
# Also currently manually putting the test date in (Need UI for this)
# Also currently manually putting in the athlete age range (Need UI for this)
# CHECK ALL SCRIPTS - since there are manuel inputs in lots of places 
# ---------------------------------------------------------------------------------

# -- IMPORTS ----------------------------------------------------------------------
import pandas as pd # For data manipulation
import numpy as np # Numpy for numerical operations
import io # For image conversion
import sys # For system operations
import pathlib # For file operations
from pathlib import Path # For file operations
from scipy import stats # For statistical operations
from datetime import datetime # For date operations
from reportlab.lib.pagesizes import letter, landscape, portrait # Reportlab for PDF generation
from reportlab.platypus import Table, TableStyle # Reportlab for tables
from reportlab.lib import colors # Reportlab for colors
from reportlab.lib.utils import ImageReader # Reportlab for image conversion
from reportlab.lib.colors import white # Reportlab for black color
from reportlab.pdfgen import canvas # Reportlab for PDF generation
from matplotlib.patches import Circle, RegularPolygon, Wedge # Matplotlib for plotting
from matplotlib.projections.polar import PolarAxes # Matplotlib for plotting
from matplotlib.projections import register_projection # Matplotlib for plotting
from matplotlib.spines import Spine # Matplotlib for plotting
from matplotlib.transforms import Affine2D # Matplotlib for plotting
from matplotlib.path import Path # Matplotlib for plotting
import matplotlib.pyplot as plt # Matplotlib for plotting
import textwrap # For wrapping text
# Add the project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------
# Add current directory to path for local imports
current_dir = pathlib.Path(__file__).parent
sys.path.insert(0, str(current_dir))

from charts import radar_factory, composite_score_chart
from ReportScripts.VALD_API.vald_client import ValdClient
from ReportScripts.VALD_API.ind_ath_data import get_athlete_data
from ReportScripts.PullRefData.pull_all import pull_all_ref

# -- CONSTANTS --------------------------------------------------------------------
# Not sure what constants we will need, or if we will need any

# TODO: Need a way to have the test date in here too 
#TEMP_TEST_SESSION = datetime(2025, 7, 1).date() # July 1, 2025 (Charles Gargus)
#TEMP_TEST_SESSION = datetime(2025, 7, 29).date() # July 29, 2025 (Dylan Tostrup)

# -- PDF GENERATION FUNCTIONS ------------------------------------------------------
def generate_athlete_pdf(athlete_name, test_date, min_age, max_age, output_path, client=None):
    if client is None:
        client = ValdClient()
    # 0.0) Data Pulling / Use
    # 0.0) Run the athlete data pull (saves to Output CSVs/Athlete/Full_Data.csv)
    athlete_data = get_athlete_data(athlete_name, test_date, client)
    # 0.1) Run the reference data pull (saves to Output CSVs/Reference/HJ_ref.csv, etc.)
    pull_all_ref(min_age, max_age)
    # 0.2) Set up the test date formatted
    test_date_formatted = test_date.strftime("%B %d, %Y")

    # 1.1) Set up the PDF canvas
    c = canvas.Canvas(output_path, pagesize=portrait(letter))
    width, height = portrait(letter)

    # 1.2) Page Formatting
    # 1.2.1) Athlete Name (above lines)
    c.setFont("Helvetica-Bold", 30) 
    c.drawString(25, height - 45, athlete_name) # (H: height - 45, height - 15)
    # 1.2.2) Outer Borders (Top and Bottom Only)
    c.setFillColorRGB(0, 0, 0) # Black
    c.rect(25, height - 58, width - 50, 8, stroke=0, fill=1) # (H: height - 58, height - 50)
    c.setFillColorRGB(0.5, 0.5, 0.5) # Grey
    c.rect(25, height - 64, width - 50, 4, stroke=0, fill=1) # (H: height - 64, height - 60)
    c.setFillColorRGB(0, 0, 0) # Black
    # 1.2.3) Performance Report Description 
    c.setFont("Helvetica", 15)
    c.drawString(25, height - 80, f"Performance Assessment Overview - {test_date_formatted}")
    # 1.2.4) Logo (TODO: Figure out where this should go)
    # 1.2.4.1) Logo Lines
    c.setFillColorRGB(0.5, 0.5, 0.5) # Grey
    c.rect(25, 40, width - 205, 4, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0) # Black
    c.rect(25, 30, width - 205, 8, stroke=0, fill=1)
    # 1.2.4.2) Logo Image
    logo_width = 72 * 2 # 72 pixels is an inch
    logo_height = 72 / 2 # 72 pixels is an inch
    logo_x = width - logo_width - 25
    logo_y = 18
    c.drawImage('Media/horizontal throwing.png', logo_x, logo_y, width=logo_width, height=logo_height, mask='auto')

    # 1.3.0) Drawing in the athlete spider chart (right side of page)
    athlete_name = athlete_name.lower().strip()
    labels = ["Reactive Strength", "Lower Half Strength", "Upper Half Strength", "Peak Power", "Relative Power"]
    # 1.3.1) Reading in the athlete data and reference data
    athlete_data = pd.read_csv("Output CSVs/Athlete/Full_Data.csv")
    hj_ref_data = pd.read_csv("Output CSVs/Reference/HJ_ref.csv")
    imtp_ref_data = pd.read_csv("Output CSVs/Reference/IMTP_ref.csv")
    ppu_ref_data = pd.read_csv("Output CSVs/Reference/PPU_ref.csv")
    cmj_ref_data = pd.read_csv("Output CSVs/Reference/CMJ_ref.csv") 
    # 1.3.2.0) HJ RSI Percentile (Reactive Strength)
    athlete_hj_rsi = round(athlete_data[athlete_data['metric_id'] == 'HJ_AVJ_RSI_Trial_']['Value'].values[0], 2)
    hj_percentile = round(stats.percentileofscore(hj_ref_data['hop_rsi_avg_best_5'], athlete_hj_rsi), 2)
    # 1.3.2.1) IMTP Peak Vertical Percentile (Lower Half Strength)
    athlete_imtp_peak = round(athlete_data[athlete_data['metric_id'] == 'IMTP_PEAK_VERTICAL_FORCE_Trial_N']['Value'].values[0], 2)  
    imtp_percentile = round(stats.percentileofscore(imtp_ref_data['PEAK_VERTICAL_FORCE_Trial_N'], athlete_imtp_peak), 2)
    # 1.3.2.2) PPU Peak Concentric Force Percentile (Upper Half Strength)
    athlete_ppu_peak = round(athlete_data[athlete_data['metric_id'] == 'PPU_PEAK_CONCENTRIC_FORCE_Trial_N']['Value'].values[0], 2)
    ppu_percentile = round(stats.percentileofscore(ppu_ref_data['PEAK_CONCENTRIC_FORCE_Trial_N'], athlete_ppu_peak), 2)
    # 1.3.2.3) CMJ Peak Power Percentile (Peak Power)
    athlete_cmj_peak = round(athlete_data[athlete_data['metric_id'] == 'CMJ_PEAK_TAKEOFF_POWER_Trial_W']['Value'].values[0], 2)
    cmj_pp_percentile = round(stats.percentileofscore(cmj_ref_data['PEAK_TAKEOFF_POWER_Trial_W'], athlete_cmj_peak), 2)
    # 1.3.2.4) CMJ Relative Power Percentile (Relative Power)
    athlete_cmj_rel = round(athlete_data[athlete_data['metric_id'] == 'CMJ_BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg']['Value'].values[0], 2)
    cmj_rp_percentile = round(stats.percentileofscore(cmj_ref_data['BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W_kg'], athlete_cmj_rel), 2)
    # 1.3.2..) ???? Anything Else? (Can add more later)
    # 1.3.3) Compiling all percentile values together
    spider_data = [hj_percentile, imtp_percentile, ppu_percentile, cmj_pp_percentile, cmj_rp_percentile]
    # 1.3.4) Creating and displaying the spider chart
    N = len(labels)
    theta = radar_factory(N, frame='polygon')
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='radar'))
    ax.set_ylim(0, 100) 
    for r in [25, 50, 75, 100]:
        points = [(angle, r) for angle in theta] + [(theta[0], r)]
        ax.plot([p[0] for p in points], [p[1] for p in points], color='gray', lw=2, alpha=0.3)
    for angle in theta:
        ax.plot([angle, angle], [0, 100], color='gray', lw=2, alpha=0.3)
    ax.plot(theta, spider_data, color="cornflowerblue", linewidth=5, marker='o', markersize=10)
    ax.fill(theta, spider_data, color="cornflowerblue", alpha=0.2)
    ax.set_varlabels(labels)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100"], fontsize=12)
    plt.tight_layout(pad=0.5)
    # 1.3.5) Saving and converting spider chart to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img = ImageReader(buf)
    c.drawImage(img, width / 2 - 25, height - 300, 270, 180, mask='auto')

    # 1.4) Displaying the spider chart data
    c.setFont("Helvetica-Bold", 10)
    spacing = 15
    top = height - 130
    c.drawString(25, top - spacing, "Reactive Strength:")
    c.drawString(25, top - 3 * spacing, "Lower Half Strength:")
    c.drawString(25, top - 5 * spacing, "Upper Half Strength:")
    c.drawString(25, top - 7 * spacing, "Peak Power:")
    c.drawString(25, top - 9 * spacing, "Relative Power:")
    c.setFont("Helvetica", 10)
    c.drawString(25, top - 2 * spacing, f"HJ Reactive Strength Index: {athlete_hj_rsi} - {hj_percentile}%")
    c.drawString(25, top - 4 * spacing, f"IMTP Peak Vertical Force: {athlete_imtp_peak}(N) - {imtp_percentile}%")
    c.drawString(25, top - 6 * spacing, f"PPU Peak Concentric Force: {athlete_ppu_peak}(N) - {ppu_percentile}%")
    c.drawString(25, top - 8 * spacing, f"CMJ Peak Power: {athlete_cmj_peak}(W) - {cmj_pp_percentile}%")
    c.drawString(25, top - 10 * spacing, f"CMJ Relative Peak Power: {athlete_cmj_rel}(W/kg) - {cmj_rp_percentile}%")

    # 1.6) Displaying the athlete's composite score
    # TODO: FIGURE OUT PROPER COMPOSITE SCORE METHOD (THIS IS NOT IT)
    # 1.6.1) Calculating the composite score
    weights = {'CMJ_BODY_WEIGHT_LBS_Trial_lb': (cmj_ref_data, 'BODY_WEIGHT_LBS_Trial_lb', 0.1),
               'CMJ_PEAK_TAKEOFF_POWER_Trial_W': (cmj_ref_data, 'PEAK_TAKEOFF_POWER_Trial_W', 0.2),
               'CMJ_CONCENTRIC_IMPULSE_Trial_Ns': (cmj_ref_data, 'CONCENTRIC_IMPULSE_Trial_Ns', 0.2),
               'CMJ_ECCENTRIC_BRAKING_IMPULSE_Trial_Ns': (cmj_ref_data, 'ECCENTRIC_BRAKING_IMPULSE_Trial_Ns', 0.18),
               'PPU_PEAK_CONCENTRIC_FORCE_Trial_N': (ppu_ref_data, 'PEAK_CONCENTRIC_FORCE_Trial_N', 0.12),
               'IMTP_PEAK_VERTICAL_FORCE_Trial_N': (imtp_ref_data, 'PEAK_VERTICAL_FORCE_Trial_N', 0.15),
               'HJ_AVJ_RSI_Trial_': (hj_ref_data, 'hop_rsi_avg_best_5', 0.05)}
    percentile_score = 0
    for metric, (temp_ref_data, temp_metric, weight) in weights.items():
        ref_series = pd.to_numeric(temp_ref_data[temp_metric], errors='coerce').dropna()
        row = athlete_data.loc[athlete_data['metric_id'] == metric, 'Value']
        temp_val = pd.to_numeric(row.iloc[0], errors='coerce')
        temp_score = stats.percentileofscore(ref_series.values, float(temp_val))
        percentile_score += temp_score * weight
    # 1.6.2) Displaying the composite score chart
    percentile_score = round(percentile_score, 2)
    composite_figure = composite_score_chart(percentile_score)
    c.drawImage(composite_figure, width / 2 + 25, 250, width=200, height=200, mask='auto')
    # 1.6.3) Description of Composite Score and Value
    # 1.6.3.1) Text Box Helper
    def draw_textbox(c, x, y, width, height, text):
        font_name = "Helvetica"
        font_size = 10
        padding = 5
        # Drawing the box
        c.setStrokeColor(white)
        c.rect(x, y - height, width, height, stroke=1, fill=0)
        # Drawing the text
        text_obj = c.beginText()
        text_obj.setTextOrigin(x + padding, y - padding - font_size)
        text_obj.setFont(font_name, font_size)
        # Wrap the text to fit within the box
        max_chars = int((width - 2 * padding) / (font_size * 0.5))
        for line in textwrap.wrap(text, max_chars):
            text_obj.textLine(line)
        c.drawText(text_obj)
    # 1.6.3.2) Information
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, 390, f"Composite Score: {percentile_score}")
    c.setFont("Helvetica", 10)
    text = ("Your composite score condenses multiple performance metrics into one simple number reflecting your overall athleticism. "
            "It shows how you rank within NextEra's in-house athletes, giving you a clear sense of where you stand. This powerful metric serves as a benchmark "
            "for tracking progress and driving performance.")
    draw_textbox(c, 20, 380, 300, 300, text)

    # 1.7) Coaches Notes
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, 220, "Coaches Notes:")
    c.setLineWidth(2)
    c.setStrokeColorRGB(0, 0, 0)
    for i in range(190,90,-25):
        c.line(25, i, width - 25, i)


    # TODO: Are we happy with the percentile composite score?
    # I guess it isn't exaclty a composite score, since it's not weighted off of all athletes
    # Probably need to figure out old composite score method (using z-scores then weighting)


 

    # Saving the PDF
    c.save()






# -- CALLING/TESTING PDF GENERATION -----------------------------------------------
# Calling an example with good data (Ace Kelly) (uncomment to run)
# temp_date = datetime(2025, 7, 1).date()
# generate_athlete_pdf("Charles Gargus", temp_date, 18, 25,"/Users/owenmccandless/Desktop/NextEra Work/CG_Example.pdf")
# generate_athlete_pdf("Dylan Tostrup", "/Users/owenmccandless/Desktop/NextEra Work/DT_Example.pdf")
temp_date = datetime(2025, 8, 3).date()
generate_athlete_pdf("Braden Thorn", temp_date, 25, 35,"/Users/owenmccandless/Desktop/NextEra Work/BT_Example.pdf")