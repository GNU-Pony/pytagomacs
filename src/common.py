#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pytagomacs – An Emacs like key–value editor library for Python

Copyright © 2013, 2014  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os



INACTIVE_COLOUR = '34'
'''
:str?  The colour of an inactive line
'''

ACTIVE_COLOUR = '01;34'
'''
:str?  The colour of an active line
'''

SELECTED_COLOUR = '44;37'
'''
:str?  The colour of a selected text
'''

STATUS_COLOUR = '07'
'''
:str?  The colour of the status bar
'''

ALERT_COLOUR = None
'''
:str?  The colour of the alert message
'''

KILLRING_LIMIT = 50
'''
:int  The maximum size of the killring
'''

EDITRING_LIMIT = 100
'''
:int  The maximum size of the editring
'''


atleast = lambda x, minimum : (x is not None) and (x >= minimum)
'''
Test that a value is defined and of at least a minimum value
'''

limit = lambda x_min, x, x_max : min(max(x_min, x), x_max)
'''
Limit a value to a closed set
'''

ctrl = lambda key : chr(ord(key) ^ ord('@'))
'''
Return the symbol for a specific letter pressed in combination with Ctrl
'''

backspace = lambda x : (ord(x) == 127) or (ord(x) == 8)
'''
Check if a key stroke is a backspace key stroke
'''



class Jump():
    '''
    Create a cursor jump that can either be included in a print statement
    as a string or invoked
    
    @param   y:int         The row, 1 based
    @param   x:int         The column, 1 based
    @string  :str|()→void  Functor that can be treated as a string for jumping
    '''
    def __init__(self, y, x):
        self.string = '\033[%i;%iH' % (y, x)
    def __str__(self):
        return self.string
    def __call__(self):
        print(self.string, end = '')


## Load extension and configurations via pytagomacsrc.
config_file = None
# Possible auto-selected configuration scripts,
# earlier ones have precedence, we can only select one.
files = []
def add_files(var, *ps, multi = False):
    if var == '~':
        try:
            # Get the home (also known as initial) directory of the real user
            import pwd
            var = pwd.getpwuid(os.getuid()).pw_dir
        except:
            return
    else:
        # Resolve environment variable or use empty string if none is selected
        if (var is None) or (var in os.environ) and (not os.environ[var] == ''):
            var = '' if var is None else os.environ[var]
        else:
            return
    paths = [var]
    # Split environment variable value if it is a multi valeu variable
    if multi and os.pathsep in var:
        paths = [v for v in var.split(os.pathsep) if not v == '']
    # Add files according to patterns
    for p in ps:
        p = p.replace('/', os.sep).replace('%', 'pytagomacs')
        for v in paths:
            files.append(v + p)
add_files('XDG_CONFIG_HOME', '/%/%rc', '/%rc')
add_files('HOME',            '/.config/%/%rc', '/.config/%rc', '/.%rc')
add_files('~',               '/.config/%/%rc', '/.config/%rc', '/.%rc')
add_files('XDG_CONFIG_DIRS', '/%rc', multi = True)
add_files(None,              '/etc/%rc')
for file in files:
    # If the file we exists,
    if os.path.exists(file):
        # select it,
        config_file = file
        # and stop trying files with lower precedence.
        break
if config_file is not None:
    code = None
    # Read configuration script file
    with open(config_file, 'rb') as script:
        code = script.read()
    # Decode configurion script file and add a line break
    # at the end to ensure that the last line is empty.
    # If it is not, we will get errors.
    code = code.decode('utf-8', 'error') + '\n'
    # Compile the configuration script,
    code = compile(code, config_file, 'exec')
    # and run it, with it have the same
    # globals as this module, so that it can
    # not only use want we have defined, but
    # also redefine it for us.
    exec(code, globals())

