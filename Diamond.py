from matplotlib import pyplot as p
from matplotlib import rc
from lattice import *

# Set up the crystal structure
lattice = FCC(3.57)
basis = Basis([('C',[0,0,0]),('C',[0.25,0.25,0.25])],l_const=3.57)
crystal = lattice + basis

# Plot a simulated XRD with copper radiation
angles, values = crystal.powder_XRD(1.54)
p.plot(angles,values)

# Add some more info to the plot
p.title(r'Simulated Powder XRD of Diamond, $\lambda = 1.54$')
p.xlabel(r'$2\theta$')
p.ylabel(r'Scattering Intensity per Cubic Angstrom')
p.show()
