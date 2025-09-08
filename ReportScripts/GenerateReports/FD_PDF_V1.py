# =================================================================================
# This script is used to generate a PDF report for a given athlete
# The report will be generated using the data from the GCP BigQuery database
# The PDF report will feature the following:
# Page 1: Athlete Name, Age, Test Date, Overall Spider Chart, and Spider Chart Data
# Page 2: Injury Risk????
# Page 3: Composite Score (for in house athletes in age range)
# =================================================================================

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
import matplotlib.pyplot as plt # Matplotlib for plotting
import textwrap # For wrapping text
import math # For mathematical operations
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
from config import MEDIA_DIR, PDF_OUTPUT_DIR

# -- CONSTANTS --------------------------------------------------------------------
# Centralized styling constants for easy layout tweaks
HEADER_FONTS = {
    "name": ("Helvetica-Bold", 30),
    "desc": ("Helvetica", 15),
    "body": ("Helvetica", 10),
}

HEADER_COLORS = {
    "border_top": (0, 0, 0),
    "border_bottom": (0.5, 0.5, 0.5),
}

LOGO_PATH = str(Path(MEDIA_DIR) / "horizontal throwing.png")
LOGO_SIZE = (72 * 2, 72 / 2)  # width, height
SPIDER_CHART_SIZE = (270, 180)
COMPOSITE_CHART_SIZE = (200, 200)


# -- DRAWING HELPERS --------------------------------------------------------------
def draw_header(c, athlete_name, test_date_formatted, width, height,
                fonts=None, colors=None, name_coords=(25, 45),
                desc_coords=(25, 80)):
    """Draw the report header with athlete name, date and borders."""
    fonts = fonts or HEADER_FONTS
    colors = colors or HEADER_COLORS
    c.setFont(*fonts["name"])
    c.drawString(name_coords[0], height - name_coords[1], athlete_name)

    # Outer borders
    c.setFillColorRGB(*colors["border_top"])
    c.rect(25, height - 58, width - 50, 8, stroke=0, fill=1)
    c.setFillColorRGB(*colors["border_bottom"])
    c.rect(25, height - 64, width - 50, 4, stroke=0, fill=1)
    c.setFillColorRGB(*colors["border_top"])

    c.setFont(*fonts["desc"])
    c.drawString(desc_coords[0], height - desc_coords[1],
                 f"Performance Assessment Overview - {test_date_formatted}")

    # Logo section
    c.setFillColorRGB(*colors["border_bottom"])
    c.rect(25, 40, width - 205, 4, stroke=0, fill=1)
    c.setFillColorRGB(*colors["border_top"])
    c.rect(25, 30, width - 205, 8, stroke=0, fill=1)
    logo_w, logo_h = LOGO_SIZE
    logo_x = width - logo_w - 25
    logo_y = 18
    c.drawImage(LOGO_PATH, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto')


def draw_spider_chart(c, width, height, spider_data, labels,
                      chart_size=SPIDER_CHART_SIZE,
                      line_color="cornflowerblue", fill_color="cornflowerblue",
                      chart_coords=None):
    """Draw the radar/spider chart representing percentile data."""
    chart_coords = chart_coords or (width / 2 - 25, height - 300)
    N = len(labels)
    theta = radar_factory(N, frame='polygon')
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='radar'))
    ax.set_ylim(0, 100)
    for r in [25, 50, 75, 100]:
        points = [(angle, r) for angle in theta] + [(theta[0], r)]
        ax.plot([p[0] for p in points], [p[1] for p in points],
                color='gray', lw=2, alpha=0.3)
    for angle in theta:
        ax.plot([angle, angle], [0, 100], color='gray', lw=2, alpha=0.3)
    ax.plot(theta, spider_data, color=line_color, linewidth=5,
            marker='o', markersize=10)
    ax.fill(theta, spider_data, color=fill_color, alpha=0.2)
    ax.set_varlabels(labels)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100"], fontsize=12)
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img = ImageReader(buf)
    c.drawImage(img, chart_coords[0], chart_coords[1],
                chart_size[0], chart_size[1], mask='auto')


def draw_textbox(c, x, y, width, height, text,
                 font_name="Helvetica", font_size=10):
    """Helper to draw a wrapped text box."""
    padding = 5
    c.setStrokeColor(white)
    c.rect(x, y - height, width, height, stroke=1, fill=0)
    text_obj = c.beginText()
    text_obj.setTextOrigin(x + padding, y - padding - font_size)
    text_obj.setFont(font_name, font_size)
    max_chars = int((width - 2 * padding) / (font_size * 0.5))
    for line in textwrap.wrap(text, max_chars):
        text_obj.textLine(line)
    c.drawText(text_obj)

def calculate_zscore_composite(athlete_data, weights):
    """Calculate a composite percentile score using weighted z-scores.

    Each metric in ``weights`` contributes a z-score that is multiplied by its
    respective weight. The weighted z-scores are summed and converted to a
    0–100 percentile scale."""

    valid_metrics = set(weights.keys())
    athlete_data = athlete_data[athlete_data["metric_id"].isin(valid_metrics)]

    used_weights = {
        metric: info
        for metric, info in weights.items()
        if metric in athlete_data["metric_id"].values
    }

    if not used_weights:
        return 0

    total_weight = sum(w for (_, _, w) in used_weights.values())
    composite_z = 0.0

    for metric, (ref_df, ref_col, weight) in used_weights.items():
        norm_weight = weight / total_weight if total_weight else 0
        ref_series = pd.to_numeric(ref_df[ref_col], errors="coerce").dropna()
        if ref_series.empty:
            continue
        ref_mean = ref_series.mean()
        ref_std = ref_series.std()
        if ref_std == 0:
            continue
        row = athlete_data.loc[athlete_data["metric_id"] == metric, "Value"]
        if row.empty:
            continue
        temp_val = pd.to_numeric(row.iloc[0], errors="coerce")
        if pd.isna(temp_val):
            continue
        z_score = (float(temp_val) - ref_mean) / ref_std
        z_score = max(min(z_score, 3), -3)
        composite_z += z_score * norm_weight

    percentile_score = stats.norm.cdf(composite_z) * 100
    return round(percentile_score, 2)

def draw_composite_score(c, width, percentile_score,
                         chart_coords=None,
                         chart_size=COMPOSITE_CHART_SIZE,
                         fonts=None, text_box=None):
    """Draw the composite score gauge and descriptive text."""
    fonts = fonts or {"title": ("Helvetica-Bold", 10),
                      "body": ("Helvetica", 10)}
    chart_coords = chart_coords or (width / 2 + 25, 250)
    text_box = text_box or (20, 380, 300, 300)

    composite_figure = composite_score_chart(percentile_score)
    c.drawImage(composite_figure, chart_coords[0], chart_coords[1],
                width=chart_size[0], height=chart_size[1], mask='auto')

    c.setFont(*fonts["title"])
    c.drawString(25, 390, f"Composite Score: {percentile_score}")
    c.setFont(*fonts["body"])
    text = ("Your composite score condenses multiple performance metrics into one simple number reflecting your overall athleticism. "
            "It shows how you rank within NextEra's in-house athletes, giving you a clear sense of where you stand. This powerful metric serves as a benchmark "
            "for tracking progress and driving performance.")
    draw_textbox(c, *text_box, text)



# -- PDF GENERATION FUNCTIONS ------------------------------------------------------
def generate_athlete_pdf(
    athlete_name,
    test_date,
    output_path,
    athlete_df,
    ref_data,
    composite_method="z_score",
):
    #0.0 format the date into a string
    test_date_formatted = test_date.strftime("%B %d, %Y")

    # 1.1) Set up the PDF canvas
    c = canvas.Canvas(str(output_path), pagesize=portrait(letter))
    width, height = portrait(letter)

    # 1.2) Page Formatting
    draw_header(c, athlete_name, test_date_formatted, width, height)


    # 1.3.0) Drawing in the athlete spider chart (right side of page)
    athlete_name = athlete_name.lower().strip()
    labels = [
        "CMJ Peak Power", 
        "CMJ Con. Imp.", 
        "CMJ Ecc. Braking RFD", 
        "PPU Peak Con. Force", 
        "PPU Ecc. Braking RFD", 
        "IMTP Peak Force", 
        "HJ RSI"]
    # 1.3.1) Reading all of the athlete data and reference data
    athlete_data = athlete_df
    imtp_ref_data = ref_data["imtp"]
    ppu_ref_data = ref_data["ppu"]
    hj_ref_data = ref_data["hj"]
    cmj_ref_data = ref_data["cmj"] 

    #Establishing body weight
    athlete_body_weight = round(athlete_data[athlete_data['metric_id'] == 'CMJ_BODY_WEIGHT_LBS_Trial_lb']['Value'].values[0], 2)
    
    # 1.3.2.0) CMJ metrics
        #Peak Power
    athlete_cmj_peak = round(athlete_data[athlete_data['metric_id'] == 'CMJ_PEAK_TAKEOFF_POWER_Trial_W']['Value'].values[0], 2)
    cmj_pp_percentile = round(stats.percentileofscore(cmj_ref_data['PEAK_TAKEOFF_POWER_Trial_W'], athlete_cmj_peak), 2)
        #Concentric Impulse
    athlete_cmj_con_imp = round(athlete_data[athlete_data['metric_id'] == 'CMJ_CONCENTRIC_IMPULSE_Trial_Ns']['Value'].values[0], 2)
    cmj_con_imp_percentile = round(stats.percentileofscore(cmj_ref_data['CONCENTRIC_IMPULSE_Trial_Ns'], athlete_cmj_con_imp), 2)
        #Eccentric Braking RFD
    athlete_cmj_eb_rfd = round(athlete_data[athlete_data['metric_id'] == 'CMJ_ECCENTRIC_BRAKING_RFD_Trial_N/s']['Value'].values[0], 2)
    cmj_eb_rfd_percentile = round(stats.percentileofscore(cmj_ref_data['ECCENTRIC_BRAKING_RFD_Trial_N_s'], athlete_cmj_eb_rfd), 2)
        #Body Mass Relative Takeoff Power
    athlete_cmj_bm_rel_peak = round(athlete_data[athlete_data['metric_id'] == 'CMJ_BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg']['Value'].values[0], 2)
    cmj_bm_rel_peak_percentile = round(stats.percentileofscore(cmj_ref_data['BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W_kg'], athlete_cmj_bm_rel_peak), 2)
    
    # 1.3.2.1) Second is PPU metrics
        #Peak Concentric Force
    athlete_ppu_peak = round(athlete_data[athlete_data['metric_id'] == 'PPU_PEAK_CONCENTRIC_FORCE_Trial_N']['Value'].values[0], 2)
    ppu_percentile = round(stats.percentileofscore(ppu_ref_data['PEAK_CONCENTRIC_FORCE_Trial_N'], athlete_ppu_peak), 2)
        #Eccentric Braking RFD
    athlete_ppu_eb_rfd = round(athlete_data[athlete_data['metric_id'] == 'PPU_ECCENTRIC_BRAKING_RFD_Trial_N/s']['Value'].values[0], 2)
    ppu_eb_rfd_percentile = round(stats.percentileofscore(ppu_ref_data['ECCENTRIC_BRAKING_RFD_Trial_N_s_'], athlete_ppu_eb_rfd), 2)
    
    # 1.3.2.2) Third is IMTP metrics
        #Peak Vertical Force
    athlete_imtp_peak = round(athlete_data[athlete_data['metric_id'] == 'IMTP_PEAK_VERTICAL_FORCE_Trial_N']['Value'].values[0], 2)  
    imtp_percentile = round(stats.percentileofscore(imtp_ref_data['PEAK_VERTICAL_FORCE_Trial_N'], athlete_imtp_peak), 2)
   
    # 1.3.2.4) Fourth is HJ metrics

    athlete_hj_rsi = round(athlete_data[athlete_data['metric_id'] == 'HJ_AVJ_RSI_Trial_']['Value'].values[0], 2)
    hj_percentile = round(stats.percentileofscore(hj_ref_data['hop_rsi_avg_best_5'], athlete_hj_rsi), 2)
   
    # 1.3.3) Compiling all percentile values together
    spider_data = [cmj_pp_percentile, cmj_con_imp_percentile, cmj_eb_rfd_percentile, ppu_percentile, ppu_eb_rfd_percentile, imtp_percentile, hj_percentile]
    # 1.3.4) Creating and displaying the spider chart
    draw_spider_chart(c, width, height, spider_data, labels)

    # 1.4) Displaying individual metric data
    spacing = 17
    top = height - 100

    def draw_underlined_text(c, x, y, text):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, text)
        text_width = c.stringWidth(text, "Helvetica-Bold", 12)
        c.setLineWidth(1)
        c.line(x, y - 2, x + text_width, y - 2)
    
    draw_underlined_text(c, 25, top - spacing, "Athlete Body Weight:")
    draw_underlined_text(c, 25, top - 3 * spacing, "Countermovement Jump Performance:")
    draw_underlined_text(c, 25, top - 8 * spacing, "Plyometric Push Up Performance:")
    draw_underlined_text(c, 25, top - 11 * spacing, "Isometric Mid Thigh Pull Performance:")
    draw_underlined_text(c, 25, top - 13 * spacing, "Hop Jump Performance:")
    c.setFont("Helvetica", 10)
    c.drawString(25, top - 2 * spacing, f"Body Weight: {athlete_body_weight} (lbs)")
    c.drawString(25, top - 4 * spacing, f"Peak Power: {athlete_cmj_peak} (W) - {cmj_pp_percentile}%")
    c.drawString(25, top - 5 * spacing, f"Concentric Impulse: {athlete_cmj_con_imp} (Ns) - {cmj_con_imp_percentile}%")
    c.drawString(25, top - 6 * spacing, f"Eccentric Braking RFD: {athlete_cmj_eb_rfd} (N/s) - {cmj_eb_rfd_percentile}%")
    c.drawString(25, top - 7 * spacing, f"Body Mass Relative Peak Power: {athlete_cmj_bm_rel_peak} (W/kg) - {cmj_bm_rel_peak_percentile}%")
    c.drawString(25, top - 9 * spacing, f"Peak Concentric Force: {athlete_ppu_peak} (N) - {ppu_percentile}%")
    c.drawString(25, top - 10 * spacing, f"Eccentric Braking RFD: {athlete_ppu_eb_rfd} (N/s) - {ppu_eb_rfd_percentile}%")
    c.drawString(25, top - 12 * spacing, f"Peak Vertical Force: {athlete_imtp_peak} (N) - {imtp_percentile}%")
    c.drawString(25, top - 14 * spacing, f"HJ Reactive Strength Index: {athlete_hj_rsi} - {hj_percentile}%")

    # 1.6) Displaying the athlete's composite score work in progress
 
    weights = {'CMJ_BODY_WEIGHT_LBS_Trial_lb': (cmj_ref_data, 'BODY_WEIGHT_LBS_Trial_lb', 0.1),
               'CMJ_PEAK_TAKEOFF_POWER_Trial_W': (cmj_ref_data, 'PEAK_TAKEOFF_POWER_Trial_W', 0.3),
               'CMJ_CONCENTRIC_IMPULSE_Trial_Ns': (cmj_ref_data, 'CONCENTRIC_IMPULSE_Trial_Ns', 0.15),
               'CMJ_ECCENTRIC_BRAKING_RFD_Trial_N/s': (cmj_ref_data, 'ECCENTRIC_BRAKING_RFD_Trial_N_s', 0.15),
               'PPU_PEAK_CONCENTRIC_FORCE_Trial_N': (ppu_ref_data, 'PEAK_CONCENTRIC_FORCE_Trial_N', 0.1),
               'IMTP_PEAK_VERTICAL_FORCE_Trial_N': (imtp_ref_data, 'PEAK_VERTICAL_FORCE_Trial_N', 0.1),
               'HJ_AVJ_RSI_Trial_': (hj_ref_data, 'hop_rsi_avg_best_5', 0.1)}
    if composite_method == "z_score":
        percentile_score = calculate_zscore_composite(athlete_data, weights)
    else:
        raise ValueError(f"Unsupported composite method: {composite_method}")
    draw_composite_score(c, width, percentile_score)

    # 1.7) Coaches Notes
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, 220, "Coaches Notes:")
    c.setLineWidth(2)
    c.setStrokeColorRGB(0, 0, 0)
    for i in range(190,90,-25):
        c.line(25, i, width - 25, i)


    # Saving the PDF
    c.save()

# -- CALLING/TESTING PDF GENERATION -----------------------------------------------
# Calling an example with good data (Ace Kelly) (uncomment to run)
# temp_date = datetime(2025, 7, 1).date()
from config import PDF_OUTPUT_DIR
from pathlib import Path
from data_loader import DataLoader


temp_date = datetime(2025, 9, 8).date()
loader = DataLoader()

loader.refresh_cache(
    "Lucas Hall",
   temp_date,
   14,
   18,
)

athlete_df, ref_data = loader.load()
generate_athlete_pdf(
    "Lucas Hall",
    temp_date,
    Path(PDF_OUTPUT_DIR) / f"LH_Example_{temp_date.strftime('%Y%m%d')}.pdf",
    athlete_df,
    ref_data,
)