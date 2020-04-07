import aeropy
import math

import numpy as np
from scipy import optimize

class shell():
    def __init__(self, geometry_parent, geometry_child,  properties,
                 bc, chord=1, ndim=2):
        """
        COnstant length is assumed for the structure

        A: metric tensor
        dA: metric tensor covariant derivative as a function of theta
        a: curvilinear basis vectors
        chord: length of the beam"""
        # Defining geometries
        self.g_p = geometry_parent
        self.g_c = geometry_child

        # shell thickness
        self.h = properties.dimensions[1]
        self.width = properties.dimensions[0]
        self.ndim = 2
        self.bc = bc
        self.properties = properties

    def kinematics_p(self, x1):
        self.g_p.basis(x1)

    def kinematics_c(self, x1):
        # define new chord
        chord = aeropy.CST_2D.calculate_c_baseline(c_L, Au_C, Au_L, deltaz)
        x1 = chord*x1
        # calculate basis vectors
        self.g_c.basis(x1)

    def calculate_chord(self, length_target = None, bounds = None):
        def f(c_c):
            length_current, err = self.g_c.arclength(c_c)
            return abs(length_target - length_current)
        if length_target is None:
            length_target, err = self.g_p.arclength()
        if bounds is None:
            self.g_c.chord = optimize.minimize(f, self.g_p.chord).x[0]
        else:
            self.g_c.chord = optimize.minimize(f, self.g_p.chord,
                                               method='L-BFGS-B',
                                               bounds = bounds).x[0]
        # In case the calculated chord is really close to the original
        if abs(self.g_p.chord - self.g_c.chord) < 1e-7:
            self.g_c.chord = self.g_p.chord

    def calculate_strains(self):
        self.gamma = 0.5*(self.g_c.A[:2, :2, :] - self.g_p.A[:2, :2, :])

    def calculate_change_curvature(self):
        self.rho = -(self.g_c.B - self.g_p.B)
        self.rho[1,1,:] = -self.properties.poisson*self.rho[0,0,:]

    def CauchyGreen(self):
        """From the definition of Hookian Thin homogeneous isentropic shell
        (Eq. 9.98a) from Wempner's book:
            - the definition uses contravariant basis vectors, but this whole
              class uses covariant basis vectors. because of that all values
              are inverted (coordinate system assumed orthogonal)"""
        self.C = np.zeros([2,2,2,2,len(self.g_c.x1_grid)])
        c0 = self.properties.young/2/(1+self.properties.poisson)
        for alpha in range(2):
            for beta in range(2):
                for gamma in range(2):
                    for eta in range(2):
                        a1 = self.g_c.A[alpha, gamma]*self.g_c.A[beta, eta]
                        a2 = self.g_c.A[alpha, eta]*self.g_c.A[beta, gamma]
                        a3 = self.g_c.A[alpha, beta]*self.g_c.A[gamma, eta]
                        c3 = (2*self.properties.poisson)/(1-self.properties.poisson)
                        self.C[alpha, beta, gamma, eta, :] = c0*(a1 + a2 + c3*a3)
                        # self.C[alpha, beta, gamma, eta, :] = self.properties.young

    def free_energy(self):
        self.phi_M = (self.h/2)*np.einsum('ijklm,ijm,klm->m',self.C,self.gamma,self.gamma)
        self.phi_B = (self.h**3/24)*np.einsum('ijklm,ijm,klm->m',self.C,self.rho,self.rho)

        self.phi =  self.phi_B + self.phi_M


    def strain_energy(self):
        # print('M', self.phi_M)
        # print('B', self.phi_B)
        self.U = self.width*np.trapz(self.phi, self.theta1)

    def work(self, steps = False):
        energy = 0
        for i in range(self.bc.concentrated_n):
            theta1 = self.g_p.arclength(self.bc.concentrated_x[i])[0]
            # print('t', theta1)
            x1_c = np.array(self.g_c.calculate_x1([theta1], output = True))
            # print('x', x1_c)
            u = self.g_c.r(x1_c) - self.g_p.r(np.array([self.bc.concentrated_x[i]]))
            # print('displacement', u)

            # print(u)
            # print(theta1, type(theta1))
            dydx = self.g_c.x3(theta1, diff='x1')
            phi = math.atan2(0.001*dydx, 0.001)
            # print(phi, math.cos(phi),math.cos(phi)*math.cos(phi), math.cos(phi)*math.sin(phi))
            loads = [0,0,0]
            load_normal = self.bc.concentrated_load[i][2]*math.cos(phi) + self.bc.concentrated_load[i][0]*math.sin(phi)
            loads[0] = -load_normal*math.sin(phi)
            loads[2] = load_normal*math.cos(phi)

            energy_u  = loads[0] * u[0][0]
            energy_w = loads[2] * u[0][2]

            for j in range(3):
                if steps:
                    # energy = self.W0 + .5*(self.load0[j] + loads[j])*(u[i][j]-self.u0[i][j])
                    # print(self.W0, loads[j], self.load0[j], u[i][j], self.u0[i][j])
                    energy += self.W0 + .5*(self.bc.concentrated_load[i][j] + self.load0[j])*(u[i][j]-self.u0[i][j])
                    # print(energy, energy_0)
                else:
                    energy += self.bc.concentrated_load[i][j]*u[i][j]
                    # energy += ( loads[j])*(u[i][j])
            energy = energy_w - energy_u
            energy_w = self.bc.concentrated_load[i][2]*u[0][2]*math.cos(phi)*math.cos(phi)
            energy_u = self.bc.concentrated_load[i][2]*u[0][0]*math.cos(phi)*math.sin(phi)
            energy = energy_w + energy_u
            print('energy', energy_u, energy_w)

        self.W = energy
        self.u = u
    def residual(self):
        self.R = self.U - self.W

    def update_parent(self):
        self.g_p.calculate_x1(self.theta1, bounds = self.g_p.bounds)
        self.g_p.basis()
        self.g_p.basis(diff = 'theta')
        self.g_p.metric_tensor()
        self.g_p.metric_tensor(diff = 'theta')
        self.g_p.curvature_tensor()

    def update_child(self, steps=False):
        self.calculate_chord(bounds = self.g_c.bounds)
        self.g_c.calculate_x1(self.theta1, bounds = self.g_c.bounds)
        self.g_c.basis()
        self.g_c.metric_tensor()
        self.calculate_strains()

        # Calculate energy
        self.g_c.basis(diff = 'theta')
        self.g_c.metric_tensor(diff = 'theta')
        self.g_c.curvature_tensor()
        self.calculate_change_curvature()
        self.CauchyGreen()
        self.free_energy()
        self.strain_energy()
        self.work(steps)
        self.residual()

    def minimum_potential(self, x0=[0,0], input_function = None,
                          bounds = np.array([[-0.01,0.01], [-0.01,0.01]]),
                          steps = False):
        def to_optimize(n_x):
            x = (bounds[:,1] - bounds[:,0])*n_x + bounds[:,0]
            self.g_c.D = input_function(x)
            self.update_child(steps=steps)
            print(self.u[0], self.R) #, self.W, self.U)
            return self.R

        if input_function is None:
            input_function = lambda x:x

        # With bounds
        n_bounds = np.array(len(bounds)*[[0,1],])
        n_x0 = (x0 - bounds[:,0])/(bounds[:,1] - bounds[:,0])
        res = optimize.minimize(to_optimize, n_x0, bounds=n_bounds, method = 'SLSQP' ) #, options = {'eps':1e-7, 'ftol':1e-7})
        x = (bounds[:,1] - bounds[:,0])*res.x + bounds[:,0]
        self.g_c.D = input_function(x)
        self.R = res.fun
        self.update_child(steps=steps)
        print('inside', x, self.W)
        if steps:
            # Updating part
            theta1 = self.g_p.arclength(self.bc.concentrated_x[0])[0]
            # print('t', theta1)
            x1_c = np.array(self.g_c.calculate_x1([theta1], output = True))
            # print('x', x1_c)
            u = self.g_c.r(x1_c) - self.g_p.r(np.array([self.bc.concentrated_x[0]]))

            self.u0 = u
            self.W0 = self.W
            self.load0 = self.bc.concentrated_load[0]
        return(x, res.fun)

    def stepped_loading(self, x0=[0,0], input_function = None,
                          bounds = np.array([[-0.01,0.01], [-0.01,0.01]]),
                          N = 2):
        load = self.bc.concentrated_load[0][2]

        self.u0 = [[0,0,0],]
        self.W0 = 0
        self.load0 = [0, 0, 0]
        coefficients = np.zeros([N,len(x0)])
        coefficients[0,:] = x0
        results = np.zeros([N,2])
        arc_lengths = np.zeros([N,2])
        arc_lengths[0,1] = self.g_p.arclength(1)[0]
        loads = np.linspace(0,load,N)
        print('loads', loads)
        for i in range(1,N):
            load_i = loads[i]
            print('load', i, load_i, self.u0, self.W0, self.load0)
            self.bc.concentrated_load[0][2] = load_i
            print(load)
            print(self.bc.concentrated_load)
            xi, residual = self.minimum_potential(x0 = x0,
                                                  input_function = input_function,
                                                  bounds = bounds, steps = True)
            coefficients[i,:] = xi
            results[i,0] = load_i
            results[i,1] = self.u0[0][2]
            arc_lengths[i,0] = load_i
            arc_lengths[i,1] = self.g_c.arclength(1)[0]
            x0 = xi
            print(results)
            print('x0', x0)

        return [coefficients, results, arc_lengths]
class design_exploration():
    def __init__(self, component):
        pass

    def sweep_geometries(self, geom_variables, input_function, reorder=None,
                         loading_condition = 'plane_stress'):
        energy_list = []
        residual_list = []
        n = len(geom_variables)
        for i in range(n):
            print(i)
            input = geom_variables[i]
            residual_list.append(self.residual(input, input_type = 'Geometry',
                                               input_function = input_function,
                                               loading_condition = loading_condition))
            energy_list.append(self.strain_energy())
        if reorder is not None:
            residual_list = np.resize(residual_list, reorder)
            energy_list = np.resize(energy_list, reorder)
        return(energy_list, residual_list)
