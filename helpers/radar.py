# radar.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import io
import base64

def radar_factory(num_vars, frame='circle'):
    """Create a radar chart with `num_vars` axes."""
    # Calculate evenly-spaced axis angles
    theta = np.linspace(0, 2*np.pi, num_vars, endpoint=False)

    class RadarAxes(PolarAxes):
        name = 'radar'
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location('N')

        def fill(self, *args, closed=True, **kwargs):
            """Override fill so that line is closed by default"""
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            """Override plot so that line is closed by default"""
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)
            return lines

        def _close_line(self, line):
            x, y = line.get_data()
            if x[0] != x[-1]:
                x = np.concatenate((x, [x[0]]))
                y = np.concatenate((y, [y[0]]))
                line.set_data(x, y)

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            if frame == 'circle':
                return Circle((0.5, 0.5), 0.5)
            elif frame == 'polygon':
                return RegularPolygon((0.5, 0.5), num_vars, radius=0.5, orientation=np.pi/2)
            else:
                raise ValueError("unknown value for 'frame': %s" % frame)

        def draw(self, renderer):
            """ Draw. If frame is polygon, make gridlines polygon-shaped """
            if frame == 'polygon':
                gridlines = self.yaxis.get_gridlines()
                for gl in gridlines:
                    gl.get_path()._interpolation_steps = num_vars
            super().draw(renderer)

        def _gen_axes_spines(self):
            if frame == 'circle':
                return super()._gen_axes_spines()
            elif frame == 'polygon':
                spine = Spine(axes=self,
                              spine_type='circle',
                              path=Path.unit_regular_polygon(num_vars))
                spine.set_transform(Affine2D().scale(.5).translate(.5, .5)
                                    + self.transAxes)
                return {'polar': spine}
            else:
                raise ValueError("unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    return theta

def plot_mental_health_radar(user_data, title='Mental Health and Wellbeing Profile'):
    """
    Create a radar chart for mental health and wellbeing dimensions.
    
    Parameters:
    -----------
    user_data : dict
        Dictionary with dimension names as keys and scores (0-10) as values.
    title : str
        Title for the radar chart.
    
    Returns:
    --------
    img_str : str
        Base64 encoded string of the image
    """
    dimensions = list(user_data.keys())
    scores = list(user_data.values())
    
    N = len(dimensions)
    theta = radar_factory(N, frame='polygon')
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='radar'))
    
    # Draw one axis per variable and add labels
    ax.set_thetagrids(np.degrees(theta), dimensions, fontsize=12)
    
    # Draw the outline of the data
    ax.plot(theta, scores, 'o-', linewidth=2, color='#5CB85C')
    ax.fill(theta, scores, alpha=0.25, color='#5CB85C')
    
    # Set y-axis limit
    ax.set_ylim(0, 10)
    
    # Add rings for reference
    ax.set_rgrids([2, 4, 6, 8, 10], angle=0, fontsize=10)
    
    # Add a title
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Add a legend
    plt.legend(['Score'], loc=(0.9, 0.9))
    
    # Adjust layout
    plt.tight_layout()
    
    # Convert plot to base64 string for embedding in HTML
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    img_str = base64.b64encode(img_data.getvalue()).decode()
    plt.close(fig)
    
    return img_str

def create_wellbeing_radar(user_data=None):
    """
    Create a radar chart for mental health and wellbeing with default dimensions.
    
    Parameters:
    -----------
    user_data : dict, optional
        Dictionary with dimension scores (0-10). If None, sample data will be used.
    
    Returns:
    --------
    img_str : str
        Base64 encoded string of the image
    """
    # Default dimensions based on the provided text
    default_dimensions = {
        "Subjective Well-Being": 0,
        "Positive Affect": 0,
        "Life Satisfaction": 0,
        "Material Living Conditions": 0,
        "Quality of Life": 0,
        "Self-acceptance": 0,
        "Positive Relations": 0,
        "Autonomy": 0,
        "Environmental Mastery": 0,
        "Purpose in Life": 0,
        "Personal Growth": 0,
        "Positive Emotion": 0,
        "Engagement": 0,
        "Relationships": 0,
        "Meaning": 0,
        "Accomplishment": 0,
        "Competence": 0,
        "Social Connections": 0,
        "Personal Security": 0
    }
    
    # If no user data is provided, create sample data
    if user_data is None:
        # Sample data
        user_data = {k: np.random.randint(3, 10) for k in default_dimensions.keys()}
    else:
        # Ensure all expected dimensions are present
        for key in default_dimensions:
            if key not in user_data:
                user_data[key] = 0
    
    return plot_mental_health_radar(user_data)
