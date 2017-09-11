#!/usr/bin/env python
from __future__ import print_function
import os
import subprocess

_mydir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
_me = os.path.basename(__file__)

tmp = os.listdir(_mydir)
examples = []
for f in tmp:
    if f.endswith('.py') and f != '__init__.py' and f != _me:
        examples.append(f)

print('Choose the example to run:')
for ex in examples:
    print('{}: {}'.format(examples.index(ex)+1, ex))

prompt = 'Enter 1--{} or q to quit: '.format(len(examples))

while True:
    user_in = raw_input(prompt)
    if user_in.lower() == 'q':
        exit(0)

    try:
        ind = int(user_in) - 1
    except ValueError:
        print('Enter a number or "q"')
    else:
        try:
            to_run = examples[ind]
        except IndexError:
            print('Must choose between 1 and {}'.format(len(examples)))
        else:
            to_run, _ = os.path.splitext(to_run)
            break

subprocess.check_call(['python', '-m', 'tutbuilder.examples.{}'.format(to_run)], cwd=os.path.join(_mydir, '..', '..'))
