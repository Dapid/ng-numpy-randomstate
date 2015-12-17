import timeit

import pandas as pd


def timer(code, setup):
    return 1000 * min(timeit.Timer(code, setup=setup).repeat(3, 10)) / 10.0


def print_legend(legend):
    print ('\n' + legend + '\n' + '*' * 40)


SETUP = '''
import {rng}

rs = {rng}.RandomState()
rs.random_sample()
'''

COMMAND = '''
rs.{dist}(1000000, method={method})
'''

COMMAND_NUMPY = '''
rs.{dist}(1000000)
'''

dist = 'standard_normal'
res = {}
for rng in ('dummy', 'pcg32', 'pcg64', 'randomkit', 'xorshift128', 'xorshift1024',
            'mrg32k3a','numpy.random'):
    for method in ('"inv"', '"zig"'):
        key = '_'.join((rng, method, dist)).replace('"','')
        command = COMMAND if 'numpy' not in rng else COMMAND_NUMPY
        if 'numpy' in rng and 'zig' in method:
            continue
        res[key] = timer(command.format(dist=dist, method=method), setup=SETUP.format(rng=rng))

s = pd.Series(res)
t = s.apply(lambda x: '{0:0.2f} ms'.format(x))
print_legend('Time to produce 1,000,000 normals')
print(t.sort_index())

p = 1000.0 / s
p = p.apply(lambda x: '{0:0.2f} million'.format(x))
print_legend('Normals per second')
print(p.sort_index())

baseline = 'numpy.random_inv_standard_normal'
p = 1000.0 / s
p = p / p[baseline] * 100 - 100
p = p.drop(baseline, 0)
p = p.apply(lambda x: '{0:0.1f}%'.format(x))
print_legend('Speed-up relative to NumPy')
print(p.sort_index())
