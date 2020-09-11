import matplotlib.pyplot as plt
from scipy.optimize import fixed_point
import numpy as np
import pickle
import os
import math
import numpy as np
from numpy.linalg import inv
import warnings

from aeropy.structural.beam import beam_chen, coupled_beams
from aeropy.structural.stable_solution import properties, loads
from aeropy.geometry.parametric import CoordinateSystem
from aeropy.geometry.airfoil import CST
from aeropy.CST_2D import calculate_c_baseline, calculate_psi_goal, calculate_spar_direction, S

g = CoordinateSystem.pCST(D=[.2, .3, .4, 1., 2., -.1], chord=[.2, .8], color=['b', 'r'],
                          N1=[1, 1], N2=[1, 1])

g.x1_grid = np.linspace(0, 1, 21)
dd = g.x3(g.x1_grid, diff='x11')
print('dd', dd)
plt.plot(g.x1_grid, dd)
plt.figure()
g.plot(label=['1', '2'])
plt.show()