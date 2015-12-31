import sys
from os import unlink
from os.path import join
from setuptools import setup, find_packages
from setuptools.extension import Extension

import numpy

from Cython.Build import cythonize

class WriteConfigExtension(Extension):
    def __init__(self, **kwargs):
        self.config_info = kwargs['config_info']
        del kwargs['config_info']
        super(Extension, WriteConfigExtension).__init__(**kwargs)



mod_dir = './randomstate'
configs = []

rngs = ['RNG_DUMMY', 'RNG_MLFG_1279_861', 'RNG_PCG32', 'RNG_PCG64', 'RNG_MT19937', 'RNG_XORSHIFT128', 'RNG_XORSHIFT1024',
        'RNG_MRG32K3A']

compile_rngs = rngs[:]

extra_defs = []
if sys.maxsize < 2 ** 33:
    compile_rngs.remove('RNG_PCG64')


def write_config(file_name, config):
    flags = config['flags']
    with open(file_name, 'w') as config:
        config.write('# Autogenerated\n\n')
        for key in flags:
            val = '1' if flags[key] else '0'
            config.write('DEF ' + key + ' = ' + val + '\n')


for rng in rngs:
    if rng not in compile_rngs:
        continue
    flags = {k: False for k in rngs}
    flags[rng] = True

    file_name = rng.lower().replace('rng_', '')
    sources = [join(mod_dir, file_name + '.pyx'),
               join(mod_dir, 'src', 'common', 'entropy.c'),
               join(mod_dir, 'core-rng.c')]
    include_dirs = [mod_dir] + [numpy.get_include()]

    if flags['RNG_PCG32']:
        sources += [join(mod_dir, 'src', 'pcg', p) for p in ('pcg-rngs-64.c', 'pcg-advance-64.c',
                                                         'pcg-output-64.c', 'pcg-output-32.c')]
        sources += [join(mod_dir, 'shims/pcg-32', 'pcg-32-shim.c')]

        defs = [('PCG_32_RNG', '1')]

        include_dirs += [join(mod_dir, 'src', 'pcg')]

    elif flags['RNG_PCG64']:
        sources += [join(mod_dir, 'src', 'pcg', p) for p in ('pcg-advance-128.c', 'pcg-rngs-128.c')]
        sources += [join(mod_dir, 'shims/pcg-64', 'pcg-64-shim.c')]

        defs = [('PCG_64_RNG', '1'), ('PCG_HAS_128BIT_OPS', '1'), ('__SIZEOF_INT128__', '16')]

        include_dirs += [join(mod_dir, 'src', 'pcg')]

    elif flags['RNG_MT19937']:
        sources += [join(mod_dir, 'src', 'random-kit', p) for p in ('random-kit.c',)]
        sources += [join(mod_dir, 'shims', 'random-kit', 'random-kit-shim.c')]

        defs = [('RANDOMKIT_RNG', '1')]

        include_dirs += [join(mod_dir, 'src', 'random-kit')]

    elif flags['RNG_XORSHIFT128']:
        sources += [join(mod_dir, 'src', 'xorshift128', 'xorshift128.c')]
        sources += [join(mod_dir, 'shims', 'xorshift128', 'xorshift128-shim.c')]

        defs = [('XORSHIFT128_RNG', '1')]

        include_dirs += [join(mod_dir, 'src', 'xorshift128')]
    elif flags['RNG_XORSHIFT1024']:
        sources += [join(mod_dir, 'src', 'xorshift1024', 'xorshift1024.c')]
        sources += [join(mod_dir, 'shims', 'xorshift1024', 'xorshift1024-shim.c')]

        defs = [('XORSHIFT1024_RNG', '1')]

        include_dirs += [join(mod_dir, 'src', 'xorshift1024')]
    elif flags['RNG_MRG32K3A']:
        sources += [join(mod_dir, 'src', 'mrg32k3a', 'mrg32k3a.c')]
        sources += [join(mod_dir, 'shims', 'mrg32k3a', 'mrg32k3a-shim.c')]

        defs = [('MRG32K3A_RNG', '1')]

        include_dirs += [join(mod_dir, 'src', 'mrg32k3a')]

    elif flags['RNG_MLFG_1279_861']:
        sources += [join(mod_dir, 'src', 'mlfg-1279-861', 'mlfg-1279-861.c')]
        sources += [join(mod_dir, 'shims', 'mlfg-1279-861', 'mlfg-1279-861-shim.c')]

        defs = [('MLFG_1279_861_RNG', '1')]

        include_dirs += [join(mod_dir, 'src', 'mlfg_1279_861')]

    elif flags['RNG_DUMMY']:
        sources += [join(mod_dir, 'src', 'dummy', 'dummy.c')]
        sources += [join(mod_dir, 'shims', 'dummy', 'dummy-shim.c')]

        defs = [('DUMMY_RNG', '1')]

        include_dirs += [join(mod_dir, 'src', 'dummy')]

    config = {'file_name': file_name,
              'sources': sources,
              'include_dirs': include_dirs,
              'defs': defs,
              'flags': {k: v for k, v in flags.items()}}

    configs.append(config)

extensions = []
# Generate files and extensions
for config in configs:
    config_file_name = join(mod_dir, config['file_name'] + '-config.pxi')
    # Rewrite core_rng to replace generic #include "config.pxi"
    with open(join(mod_dir, 'core_rng.pyx'), 'r') as original:
        with open(join(mod_dir, config['file_name'] + '.pyx'), 'w') as mod:
            for line in original:
                if line.strip() == 'include "config.pxi"':
                    line = 'include "' + config_file_name + '"\n'
                mod.write(line)

    # Write specific config file
    write_config(config_file_name, config)

    ext = cythonize([Extension('randomstate.' + config['file_name'],
              sources=config['sources'],
              include_dirs=config['include_dirs'],
              define_macros=config['defs'] + extra_defs,
              extra_compile_args=['-std=c99'])])[0]
    extensions.append(ext)

setup(name='randomstate',
      version='0.1',
      packages=find_packages(),
      package_dir={'randomstate': './randomstate'},
      license='NSCA',
      author='Kevin Sheppard',
      description='Next-gen RandoMState supporting multiple PRNGs',
      url='https://github.com/bashtage/ng-numpy-randomstate',
      long_description=open('README.md').read(),
      ext_modules=extensions,
      zip_safe=False)

# Clean up generated files
for config in configs:
    # unlink(join(mod_dir, config['file_name'] + '.pyx'))
    # unlink(join(mod_dir, config['file_name'] + '-config.pxi'))
    # unlink(join(mod_dir, config['file_name'] + '.c'))
    pass

