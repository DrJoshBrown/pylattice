from __future__ import print_function, division, unicode_literals
import numpy as n
import itertools as it

def get_form_factors():
    """
    Returns a dictionary containing the functions to calculate
    the form factor for a variety of atoms. The constants were
    sourced from the page at
    http://lamp.tu-graz.ac.at/~hadley/ss1/crystaldiffraction/atomicformfactors/formfactors.php
    """
    constants = list(n.loadtxt(
        __name__+'/form_factors.csv',
        skiprows=1,
        delimiter=',',
        usecols={1,2,3,4,5,6,7,8,9}
    ))
    labels = list(n.loadtxt(
        __name__+'/form_factors.csv',
        skiprows=1,
        delimiter=',',
        usecols={0},
        dtype='a'
    ))
    #This lambda function has stupid syntax because python
    #doesn't close over the variables until the function is
    #called, unless we include them as keyword arguments.
    form_factors = [lambda q, a1=a1,b1=b1,a2=a2,b2=b2, \
                    a3=a3,b3=b3,a4=a4,b4=b4,c=c:\
                    a1 * n.exp(-b1*(q/(4*n.pi))**2) + \
                    a2 * n.exp(-b2*(q/(4*n.pi))**2) + \
                    a3 * n.exp(-b3*(q/(4*n.pi))**2) + \
                    a4 * n.exp(-b4*(q/(4*n.pi))**2) + c
                    for a1,b1,a2,b2,a3,b3,a4,b4,c in constants]
    return {label.decode("utf-8"):form_factor
            for label, form_factor
            in zip(labels, form_factors)}
        

class Lattice(object):
    
    def __init__(self,a1,a2,a3):
        self.lattice = [n.array(a1),n.array(a2),n.array(a3)]
        self.rlattice = [
            2*n.pi*n.cross(a2,a3) /
            n.dot(a1, n.cross(a2,a3)),
            2*n.pi*n.cross(a3,a1) /
            n.dot(a2, n.cross(a3,a1)),
            2*n.pi*n.cross(a1,a2) /
            n.dot(a3, n.cross(a1,a2))
        ]

    def __add__(self,basis):
        if 'Basis' not in str(type(basis)):
            raise TypeError('A Lattice can only be added to a Basis')
        return Crystal(self,basis)



class Basis(object):
    """
    Stores a basis, defined by atomic names and sites like so:
    basis = Basis(('C',[0,0,0]),('C',[0.25,0.25,0.25]),l_const=l_const)
    It will inherit a lattice constant from whatever lattice
    it is added too
    """
    
    def __init__(self,atoms,l_const=1):
        #first_atom is included to ensure something is in the basis
        self.basis = [(atom, l_const*n.array(site)) for atom, site in atoms]


class Crystal(object):
    """
    Stores a lattice plus a basis
    """
    
    def __init__(self,lattice,basis):
        self.lattice = lattice.lattice
        self.rlattice = lattice.rlattice
        self.basis = basis.basis
        self.structure_factor = self.gen_structure_factor()
        
    def gen_structure_factor(self):
        form_factors = get_form_factors()
        if not all(atom in form_factors for atom, site in self.basis):
            raise KeyError('Specified atom has no form factor in database')
        def structure_factor(q):
            return sum([n.exp(1j*n.dot(q,site)) * \
                            form_factors[atom](n.linalg.norm(q))
                            for atom, site in self.basis])
        return structure_factor

    def powder_XRD(self,wavelength):
        """
        Generates a powder XRD spectrum for radiation with the
        given wavelength (in angstroms)
        """
        # We generate a list of accessible reciprocal lattice
        # vectors. To be accessible, the magnitude of a rlv's
        # wavevector must be less than twice that of the input
        # radiation's wavenumber.
        
        #The input wavenumber.
        nu = 2*n.pi/wavelength 
        # Now we find the shortest distance to a wall of a 
        # parallelogram "shell" in the reciprocal lattice
        min_step = min(abs(n.dot(
            (self.rlattice[0]+self.rlattice[1]
                 +self.rlattice[2]),
            n.cross(self.rlattice[i],self.rlattice[j])
            /n.linalg.norm(n.cross(self.rlattice[i],self.rlattice[j]))))
                       for i,j in [(0,1),(1,2),(2,0)])
        # If we look at all the points in this many parallelogram
        # "shells", we can't miss all the accessible wavevectors
        num_shells = int(2*nu / min_step)
        # Now we generate these possibilities
        possibilities = [(self.rlattice[0]*h + self.rlattice[1]*j
                         + self.rlattice[2]*k)
                         for h,j,k in it.product(
                                 range(-num_shells,num_shells+1),
                                 repeat=3)]
        # And we filter the possibilities, getting rid of all the
        # rlvs that are too long.
        rlvs = [rlv for rlv in possibilities if n.linalg.norm(rlv) < 2*nu]

        # Now we renormalize the intensities to account for the fact that
        # the same lattice can be described by different unit cells
        unit_vol = n.abs(n.dot(self.lattice[0],n.cross(
            self.lattice[1],self.lattice[2])))
        
        # Now we calculate the scattering intensity from each rlv
        intensities = {tuple(rlv): n.abs(self.structure_factor(rlv)/unit_vol)**2
                       for rlv in rlvs}

        # We actually only care about the magnitudes of the rlvs
        magnitudes = {}
        for rlv, intensity in intensities.items():
            repeat = False
            mag = n.linalg.norm(rlv)
            for oldmag in magnitudes:
                if n.isclose(mag,oldmag):
                    magnitudes[oldmag] += intensity
                    repeat = True
                    break
            if not repeat:
                magnitudes[mag] = intensity
        
        # Now we calculate the scattering angles and intensities
        angles = {2 * n.arcsin(mag / (2 * nu)) * 180 / n.pi:
                  intensity
                  for mag, intensity in magnitudes.items()}

        graph_angles = n.linspace(0,180,1000)
        graph_intensities = n.zeros(graph_angles.shape)
        
        for angle, intensity in angles.items():
            graph_intensities += intensity * \
                    n.exp(-(graph_angles - angle)**2 / (0.5)**2)
        
        return graph_angles, graph_intensities


    def Laue_XRD(lattice_dir, k_start, k_end):
        """
        Outputs a Laue scattering pattern given the direction
        of incident radiation, the shortest wavevector and the
        longest wavevector.
        """
        # We should use the geometric construction here: We can find all 
        # lattice vectors in the cescent. All the scattering points will
        # be in the big circle, so we just need to list the points in the
        # big circle. Which we can do by a similar method to the one
        # for powder scattering. But we should really fix that remaining bug.
        # How to find the shortest perpendicular in a parallelogram.
        pass
        

class FCC(Lattice):
    def __init__(self,l_const):
        super(FCC,self).__init__(
            l_const * n.array([0.5,0.5,0]),
            l_const * n.array([0.5,0,0.5]),
            l_const * n.array([0,0.5,0.5])
        )


class BCC(Lattice):
    def __init__(self,l_const):
        super(BCC,self).__init__(
            l_const * n.array([0.5,0.5,-0.5]),
            l_const * n.array([0.5,-0.5,0.5]),
            l_const * n.array([-0.5,0.5,0.5])
        )


class Cubic(Lattice):
    def __init__(self,l_const):
        super(Cubic,self).__init__(
            l_const * n.array([1,0,0]),
            l_const * n.array([0,1,0]),
            l_const * n.array([0,0,1])
        )
    
