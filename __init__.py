from __future__ import print_function, division
import numpy as n
import itertools as it
from matplotlib import pyplot as p

def get_form_factors():
    """
    Returns a dictionary containing the functions to calculate
    the form factor for a variety of atoms. The constants were
    sourced from the page at
    http://lamp.tu-graz.ac.at/~hadley/ss1/crystaldiffraction/atomicformfactors/formfactors.php
    """
    constants = list(n.loadtxt(
        'form_factors.csv',
        skiprows=1,
        delimiter=',',
        usecols={1,2,3,4,5,6,7,8,9}
    ))
    labels = list(n.loadtxt(
        'form_factors.csv',
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
    return {label:form_factor
            for label, form_factor
            in zip(labels, form_factors)}
        

class Lattice(object):
    
    def __init__(self,l_const,a1,a2,a3):
        self.l_const = l_const
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
    basis = Basis(('C',[0,0,0]),('C',[0.25,0.25,0.25]))
    It will inherit a lattice constant from whatever lattice
    it is added too
    """
    
    def __init__(self,first_atom,*args):
        #first_atom is included to ensure something is in the basis
        self.basis = [(first_atom[0], n.array(first_atom[1]))] + \
                     [(atom, n.array(site)) for atom, site in args]


class Crystal(object):
    """
    Stores a lattice plus a basis
    """
    
    def __init__(self,lattice,basis):
        self.l_const = lattice.l_const
        self.lattice = lattice.lattice
        self.rlattice = lattice.rlattice
        self.basis = basis.basis
        self.structure_factor = self.gen_structure_factor()
        
    def gen_structure_factor(self):
        form_factors = get_form_factors()
        if not all(atom in form_factors for atom, site in self.basis):
            raise KeyError('Specified atom has no form factor in database')
        def structure_factor(q):
            return sum(n.exp(1j*n.dot(q,self.l_const*site)) * form_factors[atom](n.linalg.norm(q))
                       for atom, site in self.basis)
        return structure_factor

    def powder_XRD(self,wavelength):
        """
        Generates a powder XRD spectrum for radiation with the
        given wavelength (in angstroms)
        """
        #First, we must generate a list of all reciprocal lattice
        # vectors within reach of the input wavelength
        nu = 2*n.pi/wavelength
        min_step = min([n.linalg.norm(a) for a in self.lattice])
        steps = int(2*nu / min_step) * 1.5 #this is a fudge right now
        


class FCC(Lattice):
    def __init__(self,l_const):
        super(FCC,self).__init__(
            l_const,
            n.array([0.5,0.5,0]),
            n.array([0.5,0,0.5]),
            n.array([0,0.5,0.5])
        )


class BCC(Lattice):
    def __init__(self,l_const):
        super(FCC,self).__init__(
            l_const,
            n.array([0.5,0.5,-0.5]),
            n.array([0.5,-0.5,0.5]),
            n.array([-0.5,0.5,0.5])
        )


class Cubic(Lattice):
    def __init__(self,l_const):
        super(FCC,self).__init__(
            l_const,
            n.array([1,0,0]),
            n.array([0,1,0]),
            n.array([0,0,1])
        )
    

lattice = FCC(5.64)
basis = Basis(('Cl',[0,0,0]),('N',[0.5,0.5,0.5]))
crystal = lattice + basis
crystal.powder_XRD(1.5406)
