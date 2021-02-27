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


def constraint_f(input):
    Au, Al = format_input(input, gu=a.bu.g, gu_p=a.bu.g_p, gl=a.bl.g, gl_p=a.bl.g_p)
    a.bu.g.D = Au
    a.bl.g.g_independent = a.bu.g
    a.bl.g.D = Al
    # length_diff = []
    # for i in range(a.bl.g.p):
    #     if a.bl.g.dependent[i]:
    #         current_length = a.bl.g.cst[i].arclength(a.bl.g.cst[i].chord)
    #         target_length = a.bl.g.cst[i].length
    #         length_diff.append(target_length-current_length)
    # offset_x = self.cst[j].offset_x + self.cst[j].chord
    a.bl.g.cst[0].chord = a.bl.g.spar_x[0]
    current_length = a.bl.g.cst[0].arclength(a.bl.g.cst[0].chord)
    target_length = a.bl.g.cst[0].length
    length_diff = target_length-current_length
    print('C', length_diff, target_length, current_length, a.bl.g.spar_x[0], a.bl.g.delta_P)
    return np.array([length_diff])


def format_u(input, g=None, g_p=None):
    return list(input)


def format_input(input, gu=None, gu_p=None, gl=None, gl_p=None):
    _, _, n_u = g_upper._check_input([])
    Au = format_u(input[:n_u], gu, gu_p)
    Al = format_u(input[n_u:], gl, gl_p)
    return Au, Al


warnings.filterwarnings("ignore", category=RuntimeWarning)


psi_spars = [0.2]
m = len(psi_spars)


n = 2
p = 2
i = n*p+1

g_upper = CoordinateSystem.pCST(D=i*[0., ],
                                chord=[psi_spars[0], 1-psi_spars[0]],
                                color=['b', 'r'], N1=[1., 1.], N2=[1., 1.],
                                offset=.05, continuity='C2', free_end=True,
                                root_fixed=True)
n = 2
p = 3
i = n*p+1

g_lower = CoordinateSystem.pCST(D=i*[0., ],
                                chord=[psi_spars[0], 0.7, 0.1],
                                color=['b', 'r', 'g'], N1=[1., 1., 1.], N2=[1., 1., 1.],
                                offset=-.05, continuity='C2', free_end=True,
                                root_fixed=True, dependent=[True, False, False],
                                length_preserving=False)

g_upper.calculate_s(N=[11, 9])
g_lower.calculate_s(N=[11, 8, 6])
p_upper = properties()
p_lower = properties()
l_upper = loads(concentrated_load=[[-np.sqrt(2)/2, -np.sqrt(2)/2]], load_s=[1])
l_lower = loads(concentrated_load=[[np.sqrt(2)/2, np.sqrt(2)/2]], load_s=[1-0.1])


a = coupled_beams(g_upper, g_lower, p_upper, p_lower, l_upper, l_lower, None,
                  None, ignore_ends=True, spars_s=psi_spars)

a.calculate_x()
constraints = ({'type': 'eq', 'fun': constraint_f})
_, _, n_u = g_upper._check_input([])
_, _, n_l = g_lower._check_input([])
# print('s0', a.bl.s0)
# print('x0', a.bl.x)
# a.formatted_residual(format_input=format_input, x0=(n_u+n_l)*[0])
# a.formatted_residual(format_input=format_input, x0=[
#                      0.00200144, 0.00350643, 0.00255035, 0.00226923] + [-0.00219846, - 0.00313221, - 0.00193564, - 0.00191324])
# a.formatted_residual(format_input=format_input, x0=(n_u+n_l)*[0])

# a.formatted_residual(format_input=format_input, x0=[
#                      0.00200144, 0.00350643, 0.00255035, 0.00226923, 0.00183999] + [-0.00219846, - 0.00313221, - 0.00193564, - 0.00191324, - 0.00127513])
# a.formatted_residual(format_input=format_input, x0=list(
# g_upper.D[:-1]) + list(g_lower.D[:1]) + list(g_lower.D[2:-1]))


# Du = [6.15460393e-05, 2.11765046e-04, 3.60480211e-04, 5.08573998e-04,
#       2.11616879e-03, 1.69337891e-03]
# Dl = [-8.76477411e-05, -2.37694753e-04, -3.86058461e-04, -1.61021055e-03,
#       -1.29029487e-03, -9.66398617e-04, -6.92314561e-07,  5.36105657e-07]
# Du = [-0.0004251407028303019, 0.0005830925145902994, 0.0002494348554951289,
#       0.0004251759025308469, 0.0021149888635737, 0.0016923557171365678]
# Dl = [-0.00031124509431450497, -0.0005866790789420483, -0.0006513744520462747, -0.0016040872875008427, -
#       0.0013324195475520374, -0.0009263075595432437, -8.113216580214986e-05, -4.477960680268073e-05]
# a.formatted_residual(format_input=format_input, x0=Du + Dl)
# constraint_f(input=Du + Dl)
a.parameterized_solver(format_input=format_input, x0=np.zeros(n_u+n_l), solver='lm')
# a.parameterized_solver(format_input=format_input, x0=np.array(Du+Dl))
# a.bu.g.D =
# a.bl.g.g_independent = a.bu.g
# a.bl.g.D = [0.0004397262495609969, 0.00022637077688929995, 1.397180190592703e-05, -0.00019761779295283623, -
#             0.00161607199242832, -0.001289298714716886, -0.0009704188068808049, 7.713376263188075e-07, 2.6771486682555207e-06]

# a.bu.g.calculate_x1(a.bu.g.s)
# a.bl.g.calculate_x1(a.bl.g.s)
# a.bu.y = a.bu.g.x3(a.bu.x)
# a.bl.y = a.bl.g.x3(a.bl.x)

print(a.bu.g.D, a.bl.g.D)
print('upper', a.bu.g.D)
print('upper 1', a.bu.g.cst[0].D)
print('upper 2', a.bu.g.cst[1].D)
print('lower', a.bl.g.D)
print('lower 1', a.bl.g.cst[0].D)
print('lower 2', a.bl.g.cst[1].D)
print('lower 3', a.bl.g.cst[2].D)
print('loads', a.bl.l.concentrated_load, a.bu.l.concentrated_load)
print('increasing', [i < j for i, j in zip(a.bl.g.x1_grid, a.bl.g.x1_grid[1:])])

plt.figure()
plt.plot(a.bu.g.x1_grid[1:], a.bu.M[1:], 'b', label='Upper')
plt.plot(a.bl.g.x1_grid[1:], a.bl.M[1:], 'r', label='Lower')

Ml = (a.bl.p.young*a.bl.p.inertia)*(a.bl.g.rho - a.bl.g_p.rho)
Mu = (a.bu.p.young*a.bu.p.inertia)*(a.bu.g.rho - a.bu.g_p.rho)
plt.plot(a.bu.g.x1_grid[1:], Mu[1:], '--b', label='Upper')
plt.plot(a.bl.g.x1_grid[1:], Ml[1:], '--r', label='Lower')
plt.legend()

# print('chords', a.bl.g.chord, a.bu.g.chord)
index = np.where(a.bl.s0 == a.spars_s[0])[0][0]
plt.figure()
plt.plot(a.bu.g_p.x1_grid, a.bu.g_p.x3(a.bu.g_p.x1_grid), 'b',
         label='Upper Parent', lw=3)
plt.plot(a.bu.g.x1_grid, a.bu.g.x3(a.bu.g.x1_grid), c='.5',
         label='Upper Child: %.3f N' % -l_upper.concentrated_load[0][-1], lw=3)
plt.plot(a.bl.g_p.x1_grid, a.bl.g_p.x3(a.bl.g_p.x1_grid), 'b', linestyle='dashed',
         label='Lower Parent', lw=3)
plt.plot(a.bl.g.x1_grid, a.bl.g.x3(a.bl.g.x1_grid), '.5', linestyle='dashed',
         label='Lower Child: %.3f N' % -l_upper.concentrated_load[0][-1], lw=3)

xu_p = np.array([a.bu.g_p.x1_grid[index]])
xl_p = np.array([a.bl.g_p.x1_grid[index]])
plt.plot([xu_p, xl_p], [a.bu.g_p.x3(xu_p), a.bl.g_p.x3(xl_p)], 'b', lw=3)
xu_c = np.array([a.bu.g.x1_grid[index]])
xl_c = np.array([a.bl.g.x1_grid[index]])
plt.plot([xu_c, xl_c], [a.bu.g.x3(xu_c), a.bl.g.x3(xl_c)], '.5', lw=3)
upper = np.loadtxt('case_study_7_upper.csv', delimiter=',')
lower = np.loadtxt('case_study_7_lower.csv', delimiter=',')
plt.scatter(upper[0, :], upper[1, :], c='.5', label='Abaqus', edgecolors='k',
            zorder=10, marker="^")
plt.scatter(lower[0, :], lower[1, :], c='.5', edgecolors='k', zorder=10,
            marker="^")
print('spars', a.bl.g.spar_x, a.bl.g.spar_y)
plt.scatter([a.bl.g.spar_x], [a.bl.g.spar_y], c='g', label='Lower spar', zorder=20, s=40)
# x = [a.bu.g.chord*a.bl.g.spar_psi_upper[0], a.bl.g.chord*a.bl.g.spar_psi[0]]
# y = [a.bu.g.chord*a.bl.g.spar_xi_upper[0], a.bl.g.chord*a.bl.g.spar_xi[0]]
# dx = x[1]-x[0]
# dy = y[1]-y[0]
# norm = math.sqrt(dx**2+dy**2)
# print('spar direction', a.bl.g.spar_directions)
# print('actual direction', dx/norm, dy/norm)
# plt.plot(x, y, c='g', label='spars', lw=3)
# plt.arrow(x[0], y[0], -a.bl.g.spar_directions[0][0]*a.bl.g.delta_P[0],
#           -a.bl.g.spar_directions[0][1]*a.bl.g.delta_P[0])
# print(a.bl.g.delta_P[0])
plt.legend()
# plt.gca().set_aspect('equal', adjustable='box')
plt.show()
