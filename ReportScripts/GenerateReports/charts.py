# =================================================================================
# This script is used to generate the charts needed for the PDF report
# Spider Chart - Overall display of FD metrics (using percentiles)
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import numpy as np
import io
from reportlab.lib.utils import ImageReader
from matplotlib.patches import Circle, RegularPolygon, Wedge # Matplotlib for plotting
from matplotlib.projections.polar import PolarAxes # Matplotlib for plotting
from matplotlib.projections import register_projection # Matplotlib for plotting
from matplotlib.spines import Spine # Matplotlib for plotting
from matplotlib.transforms import Affine2D # Matplotlib for plotting
from matplotlib.path import Path # Matplotlib for plotting
import matplotlib.pyplot as plt # Matplotlib for plotting

# -- FUNCTIONS --------------------------------------------------------------------
# Spider Chart (Change how this returns/works)
def radar_factory(num_vars, frame='polygon'):
    # Evenly spaced angles for each axis
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)
    # Generating polygonal grid lines (not circular)
    class RadarTransform(PolarAxes.PolarTransform):
        def transform_path_non_affine(self, path):
            if path._interpolation_steps > 1:
                path = path.interpolated(num_vars)
            return Path(self.transform(path.vertices), path.codes)
    # Custom axis for the chart and sets first axis to the top
    class RadarAxes(PolarAxes):
        name = 'radar'
        PolarTransform = RadarTransform
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location('N')
        # Ensures filled areas are closed by default
        def fill(self, *args, closed=True, **kwargs):
            return super().fill(closed=closed, *args, **kwargs)
        # Ensures that lines are closed by default (first point = last point)
        def plot(self, *args, **kwargs):
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)
        # Helper function to close the polygon
        def _close_line(self, line):
            x, y = line.get_data()
            if x[0] != x[-1]:
                x = np.append(x, x[0])
                y = np.append(y, y[0])
                line.set_data(x, y)
        # Setting the labels for the axes (could set these manually to make them look perfect)
        def set_varlabels(self, labels):
            r_max = self.get_ylim()[1]
            self.set_xticks(theta)
            self.set_xticklabels([])
            for label, angle in zip(labels, theta):
                angle_rad = angle
                if angle_rad == 0 or angle_rad == np.pi:
                    x = 1.1 * r_max
                else:
                    x = 1.3 * r_max
                self.text(angle_rad, x, label, size=14, horizontalalignment='center', verticalalignment='center')
        # Draws the background shape of the chart
        def _gen_axes_patch(self):
            if frame == 'circle':
                return Circle((0.5, 0.5), 0.5)
            elif frame == 'polygon':
                return RegularPolygon((0.5, 0.5), num_vars, radius=.5, edgecolor="gray", facecolor="lightgray", lw=2, alpha=0.3)
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)
        # Draws the border/spine as a circle or polygon
        def _gen_axes_spines(self):
            if frame == 'circle':
                return super()._gen_axes_spines()
            elif frame == 'polygon':
                spine = Spine(axes=self, spine_type='circle', path=Path.unit_regular_polygon(num_vars))
                spine.set_transform(Affine2D().scale(.5).translate(.5, .5) + self.transAxes)
                return {'polar': spine}
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)
    # Registers the projection and returns the angles
    register_projection(RadarAxes)
    return theta

# Composite Score Chart
def composite_score_chart(score):
    # Initializing values
    cmap_primary ="cornflowerblue"
    cmap_bg="lightgrey"
    size=(4,4)
    width=0.3
    fontsize=24
    if score == -1:
        values = [0, 100]
    else:
        values = [score, 100 - score]
    colors = [cmap_primary, cmap_bg]
    # Building figure
    fig, ax = plt.subplots(figsize=size)
    wedges, _ = ax.pie(values, colors=colors, startangle=90, counterclock=False, wedgeprops=dict(width=width, edgecolor='white'))
    ax.set_aspect("equal")
    ax.axis("off")
    # Placing score in the middle
    if score.round(0) == 45 or score == -1:
        ax.text(0, 0, "NA", ha="center", va="center", fontsize=fontsize, fontweight="bold")
    else:
        ax.text(0, 0, f"{score:.0f}", ha="center", va="center", fontsize=fontsize, fontweight="bold")
    # Saving figure to buffer and converting to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return ImageReader(buf)