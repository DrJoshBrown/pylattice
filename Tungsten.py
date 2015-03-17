from matplotlib import pyplot as p
from matplotlib import rc
rc('text', usetex=True)
from lattice import *

# Set up the crystal structure
lattice = BCC(3.155)
basis = Basis(('W',[0,0,0]))
crystal = lattice + basis

# Plot a simulated XRD with copper radiation
p.plot(*crystal.powder_XRD(1.54))

# Add some more info to the plot
p.title(r'Simulated Powder XRD of Tungsten, $\lambda = 1.54$')
p.xlabel(r'$2\theta$')
p.ylabel(r'Scattering Intensity per Cubic Angstrom')
p.show()
