# =================================================================================
# This script is used to generate a PDF report for a given athlete
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import pandas as pd # For data manipulation
import numpy as np # Numpy for numerical operations
import io # For image conversion
from reportlab.lib.pagesizes import letter, landscape # Reportlab for PDF generation
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

# Reading in important data
# 1.) Athlete Data (for athletes who need PDFs)
# 2.) Reference Data? (eventually would pull from GCP, but probably just import manually first)

# Creating the figures we need using functions
# 1.) Spider Chart (overall athleticism)
     # 1.1) Could go deeper into this and display more figures/info for each aspect of spider chart (like driveline)
# 2.) Injury Risk Gauges (doesn't work as well with only assymetrys)
# 3.) Composite Score (overall athleticism)