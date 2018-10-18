import numpy as np
from scipy.optimize import minimize


class mesh_1D():
    def __init__(self, alpha, alpha_nodes, mesh_n=10, x2=0):
        self.n = mesh_n
        self.x_p = np.linspace(0, 1, mesh_n)
        self.dx_p = 1./(mesh_n-1)
        self.alpha = alpha
        self.alpha_nodes = alpha_nodes
        self.x2 = x2

        if self.alpha_nodes[0] != 0 or self.alpha_nodes[-1] != 1:
            raise Exception('Need to define alpha_x for whole domain')

        if len(self.alpha_nodes) != len(alpha):
            raise Exception('Number of alpha nodes and values must be same')
        if list(self.alpha_nodes) != sorted(self.alpha_nodes):
            raise Exception('Alpha nodes must be in increasing order')

        self.nodes_xc = self.mesh_child()

    def mesh_child(self):
        x = self.x_p
        counter = 0
        self.x_c = self.x_p.copy()
        self.alpha_x = []
        for i in range(len(self.alpha_nodes)-1):

            alpha_i = self.alpha_nodes[i]
            alpha_f = self.alpha_nodes[i+1]
            x_filtered = x[x >= alpha_i]
            x_filtered = x_filtered[x_filtered < alpha_f]
            self.x_c[counter:counter+len(x_filtered)] = self.alpha[i]*x_filtered
            counter += len(x_filtered)
            self.alpha_x += len(x_filtered)*[self.alpha[i]]
        # Add last
        self.alpha_x.append(self.alpha[-1])
        self.alpha_x = np.array(self.alpha_x)
        self.x_c[-1] *= self.alpha[-1]


class properties():
    def __init__(self, young=70e9, poisson=.3, dimensions=[0.01, 0.01],
                 crosssection='square'):
        """Stores calculates material or structural properties. If 'square',
        dimensions = [width, height]"""
        self.young = young
        self.poisson = poisson

        if crosssection == 'square':
            self.area = dimensions[0]*dimensions[1]
            self.inertia = dimensions[0]*dimensions[1]**3/12.
        if young < 0 or poisson < 0 or poisson > 1 or self.area <= 0:
            raise Exception('Material properties need to make sense')


class boundary_conditions():
    def __init__(self, load=np.array([[10000, 0], ]), load_x=[1]):
        self.concentrated_load = load
        self.concentrated_x = load_x
        self.concentrated_n = len(load)
        self.distributed_load = None

        if len(load) != len(load_x):
            raise Exception('load values and x lists have to match')


class structure():
    def __init__(self, geometry_parent, geometry_child, mesh, properties,
                 bc, model='beam'):
        # Defining geometries
        self.g_p = geometry_parent
        self.g_c = geometry_child

        self.model = model
        self.bc = bc
        self.mesh = mesh
        self.properties = properties

    def u(self, input=None, diff=None):
        if input is not None:
            stored_x_p = self.mesh.x_p
            self.mesh.x_p = input
            self.mesh.mesh_child()

        parent = self.g_p.r(input=self.mesh.x_p, x2=self.mesh.x2,
                            input_type='x1', diff=diff)
        child = self.g_c.r(input=self.mesh.x_c, x2=self.mesh.x2,
                           input_type='x1', diff=diff)
        # Taking into consideration extension of the beam
        print('alpha', self.mesh.alpha_x)
        child[0] *= self.mesh.alpha_x

        output = child - parent

        if input is not None:
            self.mesh.x_p = stored_x_p
            self.mesh.mesh_child()
        return(output)

    def uij(self, i, j, diff=None, input_type='x1'):
        '''Indexes here are from 1 to n. So +=1 compared to rest'''
        # TODO: makes this more optimal(calculating u multiple times)
        ui_j = self.u(diff='x%i' % (j))[i-1]
        ui = self.u()[i-1]

        for l in range(1, 3):
            ui_j += self.g_c.christoffel(i, j, l, self.mesh.x_p,
                                         self.mesh.x2)*ui
        return(ui_j)

    def strain(self):
        # For cartesian
        self.epsilon = np.zeros([2, 2, self.mesh.n])
        for i in range(2):
            for j in range(2):
                ii = i + 1
                jj = j + 1
                self.epsilon[i][j] = .5*(self.uij(ii, jj) +
                                         self.uij(jj, ii))
        # christoffel_122 = self.g_c.christoffel(input, x2)
        return(self.epsilon)

    def stress(self, loading_condition='uniaxial'):
        E = self.properties.young
        nu = self.properties.poisson
        if loading_condition == 'uniaxial':
            self.sigma = E*self.epsilon
        elif loading_condition == '3D':
            self.lame = [E*nu/((1+self.poisson) * (1-2*self.poisson)),
                         E/(2*(1+self.poisson))]
            self.sigma = 2*self.lame[1]*self.epsilon
            # for main diagonal components
            for i in range(2):
                for k in range(2):
                    self.sigma[i][i] += self.lame[1]*self.epsilon[k][k]
        return(self.sigma)

    def strain_energy(self):
        energy = 0
        for i in range(len(self.sigma)):
            for j in range(len(self.sigma[i])):
                for k in range(len(self.sigma[i][j])):
                    if k == 0 or k == self.mesh.n - 1:
                        multiplier = .5*self.properties.area*self.mesh.dx_p/2.
                    else:
                        multiplier = .5*self.properties.area*self.mesh.dx_p
                    energy += multiplier*self.sigma[i][j][k]*self.epsilon[i][j][k]
        return(energy)

    def work(self):
        energy = 0
        for i in range(self.bc.concentrated_n):
            u = self.u(np.array([self.bc.concentrated_x[i]]))
            for j in range(2):
                energy += self.bc.concentrated_load[i][j] * u[j][0]
        return(energy)

    def residual(self, input=None):
        if input is not None:
            self.mesh.alpha = np.array([input])
            self.mesh.mesh_child()
            self.strain()
            self.stress()
        energy = self.strain_energy() - self.work()
        return(energy)

    def find_stable(self, x0=[0]):
        res = minimize(self.residual, x0, bounds=((-.1, .1)))
        return(res.x, res.fun)

    def sweep_geometries(self, strain_list):
        energy_list = []
        residual_list = []
        for strain in strain_list:
            self.mesh.alpha = np.array([1 + strain])
            self.mesh.mesh_child()
            self.strain()
            self.stress()
            energy_list.append(self.strain_energy())
            residual_list.append(self.residual())
        return(energy_list, residual_list)