#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
pytagomacs – An Emacs like key–value editor library for Python

Copyright © 2013  Mattias Andrée (maandree@member.fsf.org)

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


def parsefile(file):
    '''
    Parse a file name encoded with environment variables
    
    @param   file  The encoded file name
    @return        The target file name, None if the environment variables are not declared
    '''
    if '$' in file:
        buf = ''
        esc = False
        var = None
        for c in file:
            if esc:
                buf += c
                esc = False
            elif var is not None:
                if c == '/':
                    var = os.environ[var] if var in os.environ else ''
                    if len(var) == 0:
                        return None
                    buf += var + c
                    var = None
                else:
                    var += c
            elif c == '$':
                var = ''
            elif c == '\\':
                esc = True
            else:
                buf += c
        return buf
    return file


for file in ('$XDG_CONFIG_HOME/%/%rc', '$HOME/.config/%/%rc', '$HOME/.%rc', '/etc/%rc'):
    file = parsefile(file.replace('%', 'pytagomacs'))
    if (file is not None) and os.path.exists(file):
        with open(file, 'rb') as rcfile:
            code = rcfile.read().decode('utf8', 'replace') + '\n'
            env = os.environ
            code = compile(code, file, 'exec')
            exec(code, globals()) # TODO do the globals need to be set explicitly?
        break

