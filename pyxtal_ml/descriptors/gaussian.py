import numpy as np
from pymatgen.core.structure import Structure


################################ Gaussian Class ###############################


class Gaussian:
    def __init__():
        pass


############################# Auxiliary Functions #############################

def distance(arr):
    """
    L2 norm for cartesian coordinates
    """
    return np.linalg.norm(arr)
    #return ((arr[0] ** 2 + arr[1] ** 2 + arr[2] ** 2) ** 0.5)


def Kronecker(a,b):
    """
    Kronecker delta function.
    
    Parameters
    ----------
    a: int
        first index
    b: int
        second index
        
    Returns
    -------
        Return value 0 if a and b are not equal; return value 1 if a and b 
        are equal.
    -------
    """
    if a == b:
        return 1
    else:
        return 0


def dRab_dRpq(a, b, Ra, Rb, p, q):
    """
    Calculate the derivative of the norm of position vector R_{ab} with
    respect to coordinate x, y, or z denoted by q of atom with index p.

    See Eq. 14c of the supplementary information of Khorshidi, Peterson,
    CPC(2016).

    Parameters
    ----------
    a : int
        Index of the first atom.
    b : int
        Index of the second atom.
    Ra : float
        Position of the first atom.
    Rb : float
        Position of the second atom.
    p : int
        Index of the atom force is acting on.
    q : int
        Direction of force. x = 0, y = 1, and z = 2.

    Returns
    -------
    the derivative of pair atoms w.r.t. one of the atom in q direction.
    """
    Rab = np.linalg.norm(Rb - Ra)
    if p == a and a != b:  # a != b is necessary for periodic systems
        dRab_dRpq = -(Rb[q] - Ra[q]) / Rab
    elif p == b and a != b:  # a != b is necessary for periodic systems
        dRab_dRpq = (Rb[q] - Ra[q]) / Rab
    else:
        dRab_dRpq = 0
    return dRab_dRpq


def dRab_dRpq_vector(a, b, p, q):
    """
    Calculate the derivative of the position vector R_{ab} with
    respect to coordinate x, y, or z denoted by q of atom with index p.

    See Eq. 14d of the supplementary information of Khorshidi, Peterson,
    CPC(2016).

    Parameters
    ----------
    a : int
        Index of the first atom.
    b : int
        Index of the second atom.
    p : int
        Index of the atom force is acting on.
    q : int
        Direction of force. x = 0, y = 1, and z = 2.

    Returns
    -------
    list of float
        The derivative of the position vector R_{ab} with respect to atom 
        index p in direction of q.
    """
    if (p == a) or (p == b):
        dRab_dRpq_vector = [None, None, None]
        c1 = Kronecker(p, b) - Kronecker(p, a)
        dRab_dRpq_vector[0] = c1 * Kronecker(0, q)
        dRab_dRpq_vector[1] = c1 * Kronecker(1, q)
        dRab_dRpq_vector[2] = c1 * Kronecker(2, q)
        return dRab_dRpq_vector
    else:
        return [0, 0, 0]
    
    
def dcos_dRpq(a, b, c, Ra, Rb, Rc, p, q):
    """
    Calculate the derivative of cosine dot product function with respect to 
    the radius of an atom m in a particular direction l.
    
    Parameters
    ----------
    a: int
        Index of the center atom.
    b: int
        Index of the first neighbor atom.
    c: int
        Index of the second neighbor atom.
    Ra: list of floats
        Position of the center atom.
    Rb: list of floats
        Position of the first atom.
    Rc: list of floats
        Postition of the second atom.
    m: int
        Atom that is experiencing force.
    l: int
        Direction of the force.
        
    Returns
    -------
    Derivative of cosine dot product w.r.t. the radius of an atom m in a 
    particular direction l.
    """
    Rab_vector = Rb - Ra
    Rac_vector = Rc - Ra
    Rab = np.linalg.norm(Rab_vector)
    Rac = np.linalg.norm(Rac_vector)
    
    term_one = 1 / (Rab * Rac) * \
                np.dot(dRab_dRpq_vector(a, b, p, q), Rac_vector)
    term_second = 1 / (Rab * Rac) * \
                    np.dot(Rab_vector, dRab_dRpq_vector(a, c, p, q))
    term_third = np.dot(Rab_vector, Rac_vector) / Rab ** 2 / Rac * \
                    dRab_dRpq(a, b, Ra, Rb, p, q)
    term_fourth = np.dot(Rab_vector, Rac_vector) / Rab / Rac ** 2 * \
                    dRab_dRpq(a, c, Ra, Rc, p, q)
                    
    return (term_one + term_second - term_third - term_fourth)


############################## Cutoff Functional ##############################

"""
This script provides three cutoff functionals:
    1. Cosine
    2. Polynomial
    3. Hyperbolic Tangent

All cutoff functionals have an 'Rc' attribute which is the cutoff radius;
The Rc is used to calculate the neighborhood attribute. The functional will
return zero if the radius is beyond Rc.

This script is adopted from AMP:
    https://bitbucket.org/andrewpeterson/amp/src/2865e75a199a?at=master
"""


class Cosine(object):
    """
    Cutoff cosine functional suggested by Behler:
    Behler, J., & Parrinello, M. (2007). Generalized neural-network 
    representation of high-dimensional potential-energy surfaces. 
    Physical review letters, 98(14), 146401.
    (see eq. 3)
    
    Args:
        Rc(float): the cutoff radius.
    """
    def __init__(self, Rc):
        
        self.Rc = Rc
        
    def __call__(self, Rij):
        """
        Args:
            Rij(float): distance between pair atoms.
            
        Returns:
            The value (float) of the cutoff Cosine functional, will return zero
            if the radius is beyond the cutoff value.
        """
        if Rij > self.Rc:
            return 0.0
        else:
            return (0.5 * (np.cos(np.pi * Rij / self.Rc) + 1.))
        
    def derivative(self, Rij):
        """
        Calculate derivative (dF/dRij) of the Cosine functional with respect
        to Rij.
        
        Args:
            Rij(float): distance between pair atoms.
            
        Returns:
            The derivative (float) of the Cosine functional.
        """
        if Rij > self.Rc:
            return 0.0
        else:
            return (-0.5 * np.pi / self.Rc * np.sin(np.pi * Rij / self.Rc))
        
    def todict(self):
        return {'name': 'Cosine',
                'kwargs': {'Rc': self.Rc}}
        
        
class Polynomial(object):
    """
    Polynomial functional suggested by Khorshidi and Peterson:
    Khorshidi, A., & Peterson, A. A. (2016).
    Amp: A modular approach to machine learning in atomistic simulations. 
    Computer Physics Communications, 207, 310-324.
    (see eq. 9)

    Args:
        gamma(float): the polynomial power.
        Rc(float): the cutoff radius.
    """
    def __init__(self, Rc, gamma=4):
        self.gamma = gamma
        self.Rc = Rc
        
    def __call__(self, Rij):
        """
        Args:
            Rij(float): distance between pair atoms.
            
        Returns:
            The value (float) of the cutoff functional.
        """
        if Rij > self.Rc:
            return 0.0
        else:
            value = 1. + self.gamma * (Rij / self.Rc) ** (self.gamma + 1) - \
                (self.gamma + 1) * (Rij / self.Rc) ** self.gamma
            return value
        
    def derivative(self, Rij):
        """
        Derivative (dF/dRij) of the Polynomial functional with respect to Rij.
        
        Args:
            Rij(float): distance between pair atoms.
            
        Returns:
            The derivative (float) of the cutoff functional.
        """
        if Rij > self.Rc:
            return 0.0
        else:
            ratio = Rij / self.Rc
            value = (self.gamma * (self.gamma + 1) / self.Rc) * \
                (ratio ** self.gamma - ratio ** (self.gamma - 1))
        return value
    
    def todict(self):
        return {'name': 'Polynomial',
                'kwargs': {'Rc': self.Rc,
                           'gamma': self.gamma
                           }
                }
                        

class TangentH(object):
    """
    Cutoff hyperbolic Tangent functional suggested by Behler:
    Behler, J. (2015). 
    Constructing high‐dimensional neural network potentials: A tutorial review. 
    International Journal of Quantum Chemistry, 115(16), 1032-1050.
    (see eq. 7)

    Args:
        Rc(float): the cutoff radius.
    """
    def __init__(self, Rc):
        
        self.Rc = Rc
        
    def __call__(self, Rij):
        """
        Args:
            Rij(float): distance between pair atoms.
            
        Returns:
            The value (float) of the cutoff hyperbolic tangent functional, 
            will return zero if the radius is beyond the cutoff value.
        """
        if Rij > self.Rc:
            return 0.0
        else:
            return ((np.tanh(1.0 - (Rij / self.Rc))) ** 3)
        
    def derivative(self, Rij):
        """
        Calculate derivative (dF/dRij) of the hyperbolic Tangent functional 
        with respect to Rij.
        
        Args:
            Rij(float): distance between pair atoms.
            
        Returns:
            The derivative (float) of the hyberbolic tangent functional.
        """
        if Rij > self.Rc:
            return 0.0
        else:
            return (-3.0 / self.Rc * ((np.tanh(1.0 - (Rij / self.Rc))) ** 2 - \
                     (np.tanh(1.0 - (Rij / self.Rc))) ** 4))
        
    def todict(self):
        return {'name': 'TanH',
                'kwargs': {'Rc': self.Rc
                           }
                }


############################# Symmetry Functions ##############################
                

def calculate_G1(crystal, cutoff_f='Cosine', Rc=6.5):
    """
    Calculate G1 symmetry function.
    The most basic radial symmetry function using only the cutoff functional,
    the sum of the cutoff functionals for all neighboring atoms j inside the
    cutoff radius, Rc.
    
    One can refer to equation 8 in:
    Behler, J. (2015). Constructing high‐dimensional neural network 
    potentials: A tutorial review. 
    International Journal of Quantum Chemistry, 115(16), 1032-1050.

    Parameters
    ----------
    crystal: object
        Pymatgen crystal structure object.
    cutoff_f: str
        Cutoff functional. Default is Cosine functional.
    Rc: float
        Cutoff radius which the symmetry function will be calculated.
        Default value is 6.5 as suggested by Behler.
    """
    # Cutoff functional
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)
        
    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords
    
    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])
    
    G1 = []
    
    for i in range(n_core):
        G1_core = 0
        for j in range(n_neighbors):
            Rij = np.linalg.norm(core_cartesians[i] - 
                                 neighbors[i][j][0].coords)
            G1_core += func(Rij)
        G1.append(G1_core)
    
    return G1


def G1_derivative(crystal, cutoff_f='Cosine', Rc=6.5, p=1, q=0):
    '''
    Calculate the derivative of the G1 symmetry function.
    
    Args:
        crystal: object
            Pymatgen crystal structure object
        cutoff_f: str
            Cutoff functional. Default is the cosine functional
        Rc: float
            Cutoff raidus which the symmetry function will be calculated
            Default value is 6.5 angstoms
        p : int
            Index of the atom force is acting on.
        q : int
            Direction of force. x = 0, y = 1, and z = 2.
    Returns:
        G1D: float
            The value of the derivative of the G1 symmetry function.
    '''
    # Cutoff functional
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' % cutoff_f)

    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords

    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])

    G1D = []

    for i in range(n_core):
        G1D_core = 0
        for j in range(n_neighbors):
            Ri = core_cartesians[i]
            Rj = neighbors[i][j][0].coords
            Rij = np.linalg.norm(Rj - Ri)
            G1D_core += func.derivative(Rij) * \
                    dRab_dRpq(i, j, Ri, Rj, p, q)
        G1D.append(G1D_core)

    return G1D


def calculate_G2(crystal, cutoff_f='Cosine', Rc=6.5, eta=2, Rs=0.0):
    """
    Calculate G2 symmetry function.
    G2 function is a better choice to describe the radial feature of atoms in
    a crystal structure within the cutoff radius.
    
    One can refer to equation 9 in:
    Behler, J. (2015). Constructing high‐dimensional neural network 
    potentials: A tutorial review. 
    International Journal of Quantum Chemistry, 115(16), 1032-1050.

    Parameters
    ----------
    crystal: object
        Pymatgen crystal structure object.
    cutoff_f: str
        Cutoff functional. Default is Cosine functional.
    Rc: float
        Cutoff radius which the symmetry function will be calculated.
        Default value is 6.5 as suggested by Behler.
    eta: float
        The parameter of G2 symmetry function.
    Rs: float
        Determine the shift from the center of the Gaussian.
        Default value is zero.

    Returns
    -------
    G2 : float
        G2 symmetry value.
    """
    # Cutoff functional
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)
    
    # Get positions of core atoms
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords
    
    # Their neighbors within the cutoff radius
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])
    
    G2 = []

    for i in range(n_core):
        G2_core = 0
        for j in range(n_neighbors):
            Rij = np.linalg.norm(core_cartesians[i] - 
                                 neighbors[i][j][0]._coords)
            G2_core += np.exp(-eta * Rij ** 2. / Rc ** 2.) * func(Rij)
        G2.append(G2_core)
    
    return G2


def G2_derivative(crystal, cutoff_f='Cosine', Rc=6.5, eta=2, Rs=0.0, p=1, q=0):
    '''
    Calculate the derivative of the G2 symmetry function.
    
    Args:
        crystal: object
            Pymatgen crystal structure object
        cutoff_f: str
            Cutoff functonal. Default cosine functional
        Rc: float
            Cutoff radius for symmetry function, defauly 6.5 angstoms
        eta: float
            The parameter for the G2 symmetry function
        Rs: float
            Determine the shift from the center of the gaussian, default= 0
    Returns:
        G2D: float
            The derivative of G2 symmetry function
    '''
    # Cutoff functional
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)

    # Get positions of core atoms
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords

    # Their neighbors within the cutoff radius
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])

    G2D = []

    for i in range(n_core):
        G2D_core = 0
        for j in range(n_neighbors):
            Ri = core_cartesians[i]
            Rj = neighbors[i][j][0]._coords
            Rij = np.linalg.norm(Rj - Ri)
            G2D_core += np.exp(-eta * (Rij - Rs)**2) * \
                        dRab_dRpq(i, j, Ri, Rj, p, q) * \
                        (-2 * eta * (Rij - Rs) * func(Rij) + 
                         func.derivative(Rij))
        G2D.append(G2D_core)

    return G2D


def calculate_G3(crystal, cutoff_f='Cosine', Rc=6.5, k=10):
    """
    Calculate G3 symmetry function.
    G3 function is a damped cosine functions with a period length described by
    K. For example, a Fourier series expansion a suitable description of the 
    radial atomic environment can be obtained by comibning several G3
    functions with different values for K.
    Note: due to the distances of atoms, G3 can cancel each other out depending
    on the positive and negative value.
    
    One can refer to equation 7 in:
    Behler, J. (2011). Atom-centered symmetry functions for constructing 
    high-dimensional neural network potentials. 
    The Journal of chemical physics, 134(7), 074106.
    
    Parameters
    ----------
    crystal: object
        Pymatgen crystal structure object.
    cutoff_f: str
        Cutoff functional. Default is Cosine functional.
    Rc: float
        Cutoff radius which the symmetry function will be calculated.
        Default value is 6.5 as suggested by Behler.
    k: float
        The Kappa value as G3 parameter.
    
    Returns
    -------
    G3: float
        G3 symmetry value
    """
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)
    
    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords
    
    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])
    
    G3 = []
    
    for i in range(n_core):
        G3_core = 0
        for j in range(n_neighbors):
            Rij = np.linalg.norm(core_cartesians[i] - 
                                 neighbors[i][j][0].coords)
            G3_core += np.cos(k * Rij / Rc) * func(Rij)
        G3.append(G3_core)
    
    return G3


def G3_derivative(crystal, cutoff_f='Cosine', Rc=6.5, k=10, p=1, q=0):
    '''
    Calculate derivative of the G3 symmetry function.
    
    Args:
        crystal: object
            Pymatgen crystal structure object.
        cutoff_f: str
            Cutoff functional. Default is Cosine functional.
        Rc: float
            Cutoff radius which the symmetry function will be calculated.
            Default value is 6.5 as suggested by Behler.
        k: float
            The Kappa value as G3 parameter.
    Returns:
        G3D: float
            Derivative of G3 symmetry function
    '''
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' % cutoff_f)

    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords

    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])

    G3D = []

    for i in range(n_core):
        G3D_core = 0
        for j in range(n_neighbors):
            Ri = core_cartesians[i]
            Rj = neighbors[i][j][0].coords
            Rij = np.linalg.norm(Rj - Ri)
            G3D_core += (np.cos(k * Rij) * func.derivative(Rij) - \
                         k * np.sin(k * Rij) * func(Rij)) * \
                         dRab_dRpq(i, j, Ri, Rj, p, q)
        G3D.append(G3D_core)

    return G3D


def calculate_G4(crystal, cutoff_f='Cosine', Rc=6.5, eta=2, lamBda=1, zeta=1):
    """
    Calculate G4 symmetry function.
    G4 function is an angular function utilizing the cosine funtion of the
    angle theta_ijk centered at atom i.

    One can refer to equation 8 in:
    Behler, J. (2011). Atom-centered symmetry functions for constructing 
    high-dimensional neural network potentials. 
    The Journal of chemical physics, 134(7), 074106.
    
    Parameters
    ----------
    crystal: object
        Pymatgen crystal structure object.
    cutoff_f: str
        Cutoff functional. Default is Cosine functional.
    Rc: float
        Cutoff radius which the symmetry function will be calculated.
        Default value is 6.5 as suggested by Behler.
    eta: float
        The parameter of G4 symmetry function.
    lamBda: float
        LamBda take values from -1 to +1 shifting the maxima of the cosine
        function to 0 to 180 degree.
    zeta: float
        The angular resolution. Zeta with high values give a narrower range of
        the nonzero G4 values. Different zeta values is preferrable for
        distribution of angles centered at each reference atom. In some sense,
        zeta is illustrated as the eta value.
        
    Returns
    -------
    G4: float
        G4 symmetry value
    """
    # Cutoff functional
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)
    
    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords
    
    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])
    
    G4 = []
    for i in range(n_core):
        G4_core = 0.0
        for j in range(n_neighbors-1):
            for k in range(j+1, n_neighbors):
                Ri = core_cartesians[i]
                Rj = neighbors[i][j][0].coords
                Rk = neighbors[i][k][0].coords
                
                Rij_vector = Rj - Ri
                Rij = np.linalg.norm(Rij_vector)
                
                Rik_vector = Rk - Ri
                Rik = np.linalg.norm(Rik_vector)
                
                Rjk_vector = Rk - Rj
                Rjk = np.linalg.norm(Rjk_vector)
                
                cos_ijk = np.dot(Rij_vector, Rik_vector)/ Rij / Rik
                term = (1. + lamBda * cos_ijk) ** zeta
                term *= np.exp(-eta * (Rij ** 2. + Rik ** 2. + Rjk ** 2.) /
                               Rc ** 2.)
                term *= func(Rij) * func(Rik) * func(Rjk)
                G4_core += term
        G4_core *= 2. ** (1. - zeta)
        G4.append(G4_core)
        
    return G4


def G4_derivative(crystal, cutoff_f='Cosine', 
                  Rc=6.5, eta=2, lamBda=1, zeta=1, p=1, q=0):
    """
    Calculate the derivative of the G4 symmetry function.
    
    Parameters
    ----------
    crystal: object
        Pymatgen crystal structure object.
    cutoff_f: str
        Cutoff functional. Default is Cosine functional.
    Rc: float
        Cutoff radius which the symmetry function will be calculated.
        Default value is 6.5 as suggested by Behler.
    eta: float
        The parameter of G4 symmetry function.
    lamBda: float
        LamBda take values from -1 to +1 shifting the maxima of the cosine
        function to 0 to 180 degree.
    zeta: float
        The angular resolution. Zeta with high values give a narrower range of
        the nonzero G4 values. Different zeta values is preferrable for
        distribution of angles centered at each reference atom. In some sense,
        zeta is illustrated as the eta value.

    Returns
    -------
    G4D: float
        The derivative of G4 symmetry function
    """
    # Cutoff functional
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)
        
    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords
    
    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])
    
    G4D = []
    for i in range(n_core):
        G4D_core = 0.0
        for j in range(n_neighbors-1):
            for k in range(j+1, n_neighbors):
                Ri = core_cartesians[i]
                Rj = neighbors[i][j][0].coords
                Rk = neighbors[i][k][0].coords
                
                Rij_vector = Rj - Ri
                Rij = np.linalg.norm(Rij_vector)
                
                Rik_vector = Rk - Ri
                Rik = np.linalg.norm(Rik_vector)
                
                Rjk_vector = Rk - Rj
                Rjk = np.linalg.norm(Rjk_vector)
                
                cos_ijk = np.dot(Rij_vector, Rik_vector)/ Rij / Rik
                dcos_ijk = dcos_dRpq(i, j, k, Ri, Rj, Rk, p, q)
                
                cutoff = func(Rij) * func(Rik) * func(Rjk)
                cutoff_Rik_Rjk = func(Rik) * func(Rjk)
                cutoff_Rij_Rjk = func(Rij) * func(Rjk)
                cutoff_Rij_Rik = func(Rij) * func(Rik)
                
                cutoff_Rij_derivative = func.derivative(Rij) * \
                                        dRab_dRpq(i, j, Ri, Rj, p, q)
                cutoff_Rik_derivative = func.derivative(Rik) * \
                                        dRab_dRpq(i, k, Ri, Rk, p, q)
                cutoff_Rjk_derivative = func.derivative(Rjk) * \
                                        dRab_dRpq(j, k, Rj, Rk, p, q)

                lamBda_term = 1 + lamBda * cos_ijk
                
                first_term = lamBda * zeta * dcos_ijk
                first_term += -2 * zeta * lamBda_term / Rc ** 2 * \
                                (Rij * dRab_dRpq(i, j, Ri, Rj, p, q) + 
                                 Rik * dRab_dRpq(i, k, Ri, Rk, p, q) +
                                 Rjk * dRab_dRpq(j, k, Rj, Rk, p, q))
                first_term *= cutoff
                
                second_term = cutoff_Rij_derivative * cutoff_Rik_Rjk + \
                                    cutoff_Rik_derivative * cutoff_Rij_Rjk + \
                                    cutoff_Rjk_derivative * cutoff_Rij_Rik                
                second_term *= lamBda_term
                
                term = first_term + second_term
                term *= lamBda_term ** (zeta - 1)
                term *= np.exp(-eta * (Rij ** 2. + Rik ** 2. + Rjk ** 2.) /
                               Rc ** 2.)
                
                G4D_core += term

        G4D_core *= 2. ** (1. - zeta)
        G4D.append(G4D_core)
        
    return G4D
    

def calculate_G5(crystal, cutoff_f='Cosine', Rc=6.5, eta=2, lamBda=1, zeta=1):
    """
    Calculate G5 symmetry function.
    G5 function is also an angular function utilizing the cosine funtion of the
    angle theta_ijk centered at atom i. The difference between G5 and G4 is 
    that G5 does not depend on the Rjk value. Hence, the G5 will generate a 
    greater value after the summation compared to G4.

    One can refer to equation 9 in:
    Behler, J. (2011). Atom-centered symmetry functions for constructing 
    high-dimensional neural network potentials. 
    The Journal of chemical physics, 134(7), 074106.
    
    Parameters
    ----------
    crystal: object
        Pymatgen crystal structure object.
    cutoff_f: str
        Cutoff functional. Default is Cosine functional.
    Rc: float
        Cutoff radius which the symmetry function will be calculated.
        Default value is 6.5 as suggested by Behler.
    eta: float
        The parameter of G5 symmetry function.
    lamBda: float
        LamBda take values from -1 to +1 shifting the maxima of the cosine
        function to 0 to 180 degree.
    zeta: float
        The angular resolution. Zeta with high values give a narrower range of
        the nonzero G4 values. Different zeta values is preferrable for
        distribution of angles centered at each reference atom. In some sense,
        zeta is illustrated as the eta value.
        
    Returns
    -------
    G5: float
        G5 symmetry value
    """    
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)
    
    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords
    
    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])
    
    G5 = []
    for i in range(n_core):
        G5_core = 0.0
        for j in range(n_neighbors-1):
            for k in range(j+1, n_neighbors):
                Rij_vector = core_cartesians[i] - neighbors[i][j][0].coords
                Rij = np.linalg.norm(Rij_vector)
                Rik_vector = core_cartesians[i] - neighbors[i][k][0].coords
                Rik = np.linalg.norm(Rik_vector)
                cos_ijk = np.dot(Rij_vector, Rik_vector)/ Rij / Rik
                term = (1. + lamBda * cos_ijk) ** zeta
                term *= np.exp(-eta * (Rij ** 2. + Rik ** 2.) / Rc ** 2.)
                term *= func(Rij) * func(Rik)
                G5_core += term
        G5_core *= 2. ** (1. - zeta)
        G5.append(G5_core)
        
    return G5


def G5_derivative(crystal, cutoff_f='Cosine', 
                  Rc=6.5, eta=2, lamBda=1, zeta=1, p=1, q=0):
    """
    Calculate the derivative of the G5 symmetry function.
    
    Parameters
    ----------
    crystal: object
        Pymatgen crystal structure object.
    cutoff_f: str
        Cutoff functional. Default is Cosine functional.
    Rc: float
        Cutoff radius which the symmetry function will be calculated.
        Default value is 6.5 as suggested by Behler.
    eta: float
        The parameter of G5 symmetry function.
    lamBda: float
        LamBda take values from -1 to +1 shifting the maxima of the cosine
        function to 0 to 180 degree.
    zeta: float
        The angular resolution. Zeta with high values give a narrower range of
        the nonzero G5 values. Different zeta values is preferrable for
        distribution of angles centered at each reference atom. In some sense,
        zeta is illustrated as the eta value.

    Returns
    -------
    G5D: float
        The derivative of G5 symmetry function
    """
    if cutoff_f == 'Cosine':
        func = Cosine(Rc=Rc)
    elif cutoff_f == 'Polynomial':
        func = Polynomial(Rc=Rc)
    elif cutoff_f == 'TangentH':
        func = TangentH(Rc=Rc)
    else:
        raise NotImplementedError('Unknown cutoff functional: %s' %cutoff_f)
        
    # Get core atoms information
    n_core = crystal.num_sites
    core_cartesians = crystal.cart_coords
    
    # Get neighbors information
    neighbors = crystal.get_all_neighbors(Rc)
    n_neighbors = len(neighbors[1])
    
    G5D = []
    for i in range(n_core):
        G5D_core = 0.0
        for j in range(n_neighbors-1):
            for k in range(j+1, n_neighbors):
                Ri = core_cartesians[i]
                Rj = neighbors[i][j][0].coords
                Rk = neighbors[i][k][0].coords
                
                Rij_vector = Rj - Ri
                Rik_vector = Rk - Ri
                Rij = np.linalg.norm(Rij_vector)
                Rik = np.linalg.norm(Rik_vector)
                
                cos_ijk = np.dot(Rij_vector, Rik_vector)/ Rij / Rik
                dcos_ijk = dcos_dRpq(i, j, k, Ri, Rj, Rk, p, q)
                
                cutoff = func(Rij) * func(Rik)
                cutoff_Rij_derivative = func.derivative(Rij) * \
                                        dRab_dRpq(i, j, Ri, Rj, p, q)
                cutoff_Rik_derivative = func.derivative(Rik) * \
                                        dRab_dRpq(i, k, Ri, Rk, p, q)

                lamBda_term = 1 + lamBda * cos_ijk
                
                first_term = -2 * eta / Rc ** 2 * lamBda_term * \
                                (Rij * dRab_dRpq(i, j, Ri, Rj, p, q) + 
                                 Rik * dRab_dRpq(i, k, Ri, Rk, p, q))
                first_term += lamBda * zeta * dcos_ijk
                first_term *= cutoff
                
                second_term = lamBda_term * \
                                (cutoff_Rij_derivative * func(Rik) + 
                                 cutoff_Rik_derivative * func(Rij))
                                
                term = first_term + second_term
                term *= lamBda_term ** (zeta - 1)
                term *= np.exp(-eta * (Rij ** 2. + Rik ** 2.) /
                               Rc ** 2.)
                                
                G5D_core += term

        G5D_core *= 2. ** (1. - zeta)
        G5D.append(G5D_core)
        
    return G5D


crystal = Structure.from_file('POSCARs/POSCAR-NaCl')
print(G1_derivative(crystal))
print(G2_derivative(crystal))
print(G3_derivative(crystal))
print(G4_derivative(crystal))
print(G5_derivative(crystal))
