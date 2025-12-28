import warnings
from astropy.utils.exceptions import AstropyWarning

# Suppress specific Astropy warnings
warnings.filterwarnings('ignore', category=AstropyWarning)
warnings.filterwarnings('ignore', message='.*transforming other coordinates.*')
