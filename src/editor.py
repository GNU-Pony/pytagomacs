#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
featherweight – A lightweight terminal news feed reader

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
import sys
from subprocess import Popen, PIPE


def limit(min_value, value, max_value):
    '''
    Limit a value to a closed set
    
    @param  min_value  Minimum value
    @param  value      Preferred value
    @param  max_value  Maximum value
    '''
    return min(max(min_value, value), max_value)


def ctrl(key):
    '''
    Return the symbol for a specific letter pressed in combination with Ctrl
    
    @param   key  Without Ctrl
    @return       With Ctrl
    '''
    return chr(ord(key) - ord('@'))


class jump(): ## Lowercase
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


class TextArea():
    '''
    GNU Emacs alike text area
    '''
    
    def __init__(self, fields, datamap, left, top, width, height):
        '''
        Constructor
        
        @param  fields:list<str>        Field names
        @param  datamap:dist<str, str>  Data map
        @param  left:int                Left position of the component
        @param  top:int                 Top position of the component
        @param  width:int               Width of the component
        @param  height:int              Height of the component
        '''
        self.fields, self.datamap, self.left, self.top, self.width, self.height = fields, datamap, left, top, width - 1, height
        self.innerleft = len(max(self.fields, key = len)) + 3
        self.lines = [TextArea.Line(self, self.fields[y], self.datamap[self.fields[y]], y) for y in range(len(self.fields))]
        self.areawidth = self.width - self.innerleft - self.left + 1
        self.killring, self.killmax, self.killptr = [], 50, 0
        self.y, self.x, self.offx, self.mark = 0, 0, 0, None
        self.last_alert, self.last_status, self.alerted = None, None, False
    
    
    
    def get_selection(self, for_display = False):
        a = min(self.mark, self.x)
        b = max(self.mark, self.x)
        if for_display:
            a = limit(0, a - self.offx, self.areawidth)
            b = limit(0, b - self.offx, self.areawidth)
        return (a, b)
    
    
    class Line():
        def __init__(self, area, name, text, y):
            self.area, self.name, self.text, self.y = area, name, text, y
        
        def draw(self):
            leftside = '%s\033[%s34m%s:\033[00m' % (jump(self.area.top + self.y, self.area.left), '01;' if self.area.y == self.y else '', self.name)
            text = (self.text[self.area.offx if self.area.y == self.y else 0:] + ' ' * self.area.areawidth)[:self.area.areawidth]
            if (self.area.y == self.y) and (self.area.mark is not None) and (self.area.mark >= 0):
                (a, b) = self.area.get_selection(True)
                if a != b:
                    text = text[:a] + ('\033[44;37m%s\033[00m' % text[a : b]) + text[b:]
            print('%s%s%s' % (leftside, jump(self.area.top + self.y, self.area.left + self.area.innerleft), text), end='')
        
        def copy(self):
            if (self.area.mark is not None) and (self.area.mark >= 0) and (self.area.mark != self.area.x):
                (a, b) = self.area.get_selection()
                self.area.killring.append(self.text[a : b])
                if len(self.area.killring) > self.area.killmax:
                    self.area.killring[:] = self.area.killring[1:]
                (a, b) = self.area.get_selection(True)
                text = self.text[self.area.offx:][:self.area.areawidth][a : b]
                print('%s%s' % (jump(self.area.top + self.y, self.area.left + self.area.innerleft + a), text), end='')
                self.area.mark = None
                return True
            else:
                return False
        
        def cut(self):
            mark, x = self.area.mark, self.area.x
            if self.copy():
                self.area.mark, self.area.x = mark, x
                self.delete()
                return True
            else:
                return False
        
        def kill(self):
            if self.area.x < len(self.text):
                self.area.mark = len(self.text)
                self.cut()
                return True
            else:
                return False
        
        def delete(self):
            removed = 0
            if (self.area.mark is not None) and (self.area.mark >= 0) and (self.area.mark != self.area.x):
                (a, b) = self.area.get_selection()
                self.text = self.text[:a] + self.text[b:]
                self.area.x = a
                if self.area.offx > len(self.text):
                    self.area.offx = max(len(self.text) - self.area.areawidth, 0)
                    self.area.mark = None
                    print('%s%s' % (jump(self.area.top + self.y, self.area.left + self.area.innerleft), ' ' * self.area.areawidth), end='')
                    self.draw()
                    return True
                removed = b - a
            self.area.mark = None
            if removed == 0:
                if self.area.x == len(self.text):
                    return False
                removed = 1
                self.text = self.text[:self.area.x] + self.text[self.area.x + 1:]
            text = self.text[self.area.offx:][:self.area.areawidth]
            a = limit(0, self.area.x - self.area.offx, self.area.areawidth)
            left = self.area.left + self.area.innerleft + a
            print('%s%s%s' % (jump(self.area.top + self.y, left), text[a:] + ' ' * removed, jump(self.area.top + self.y, left)), end='')
            return True
        
        def erase(self):
            if not ((self.area.mark is not None) and (self.area.mark >= 0) and (self.area.mark != self.area.x)):
                self.area.mark = None
                if self.area.x == 0:
                    return False
                self.area.x -= 1
                if self.area.x < self.area.offx:
                    self.area.offx = max(self.area.offx - self.area.areawidth, 0)
                    self.draw()
                    jump(self.area.top + self.y, self.area.left + self.area.innerleft + self.area.x - self.area.offx)()
            self.delete()
            return True
        
        def yank(self, resetptr = True):
            if len(self.area.killring) == 0:
                return False
            self.area.mark = None
            if resetptr:
                self.area.killptr = len(self.area.killring) - 1
            yanked = self.area.killring[self.area.killptr]
            self.text = self.text[:self.area.x] + self.area.killring[self.area.killptr] + self.text[self.area.x:]
            self.area.x += len(yanked)
            if self.area.x > self.area.offx + self.area.areawidth:
                self.area.offx = len(self.text) - self.area.areawidth
            print('%s%s' % (jump(self.area.top + self.y, self.area.left + self.area.innerleft), ' ' * self.area.areawidth), end='')
            self.draw()
            jump(self.area.top + self.y, self.area.left + self.area.innerleft + self.area.x - self.area.offx)()
            return True
        
        def yank_cycle(self):
            if len(self.area.killring) == 0:
                return False
            yanked = self.area.killring[self.area.killptr]
            if self.text[max(self.area.x - len(yanked), 0) : self.area.x] != yanked:
                return False
            self.area.mark = self.area.x - len(yanked)
            self.delete()
            self.area.killptr -= 1
            self.yank(self.area.killptr < 0)
            return True
        
        def move_point(self, delta):
            x = self.area.x + delta
            if 0 <= x <= len(self.text):
                self.area.x = x
                if delta < 0:
                    if self.area.offx > self.area.x:
                        self.area.offx = self.area.x - self.area.areawidth
                        self.area.offx = max(self.area.offx, 0)
                        self.draw()
                        jump(self.area.top + self.y, self.area.left + self.area.innerleft + self.area.x - self.area.offx)()
                    else:
                        print('\033[%iD' % -delta, end='')
                elif delta > 0:
                    if self.area.x - self.area.offx > self.area.areawidth:
                        self.area.offx = self.area.x
                        self.draw()
                        jump(self.area.top + self.y, self.area.left + self.area.innerleft)()
                    else:
                        print('\033[%iC' % delta, end='')
                return delta != 0
            return False
        
        def swap_mark(self):
            if (self.area.mark is not None) and (self.area.mark >= 0):
                self.area.mark, self.area.x = self.area.x, self.area.mark
                return True
            else:
                return False
        
        def override(self, insert, override = True):
            if (self.area.mark is not None) and (self.area.mark >= 0):
                self.area.mark = ~(self.area.mark)
            if len(insert) == 0:
                return
            a, b = self.area.x, self.area.x
            if override:
                b = min(self.area.x + len(insert), len(self.text))
            self.text = self.text[:a] + insert + self.text[b:]
            oldx = self.area.x
            self.area.x += len(insert)
            if self.area.x - self.area.offx < self.area.areawidth:
                if not override:
                    y = self.area.top + self.y
                    xi = self.area.left + self.area.innerleft
                    print('%s\033[%iP' % (jump(y, xi + self.area.areawidth - len(insert)), len(insert)), end='')
                    print('%s\033[%i@' % (jump(y, xi + oldx - self.area.offx), len(insert)), end='')
                print(insert, end='')
            else:
                self.area.offx = len(self.text) - self.area.areawidth
                jump(self.area.top + self.y, self.area.left + self.area.innerleft)
                print(' ' * self.area.areawidth, end='')
                self.draw()
                jump(self.area.top + self.y, self.area.left + self.area.innerleft + self.area.x - self.area.offx)()
        
        def insert(self, insert):
            self.override(insert, False)
    
    
    
    def status(self, text):
        '''
        Print a message to the status bar
        
        @param  text:str  The message
        '''
        txt = ' (' + text + ') '
        y = self.top + self.y
        x = self.left + self.innerleft + self.x - self.offx
        print('%s\033[7m%s-\033[27m%s' % (jump(self.height - 1, 1), txt + '-' * (self.width - len(txt)), jump(y, x)), end='')
        self.last_status = text
    
    def alert(self, text):
        '''
        Print a message to the alert bar
        
        @param  text:str  The message
        '''
        if text is None:
            self.alert('')
            self.alerted = False
        else:
            y = self.top + self.y
            x = self.left + self.innerleft + self.x - self.offx
            print('%s\033[2K%s%s' % (jump(self.height, 1), text, jump(y, x)), end='')
            self.alerted = True
        self.last_alert = text
    
    def restatus(self):
        '''
        Reprint the status bar
        '''
        self.status(self.last_status)
    
    def realert(self):
        '''
        Reprint the alert bar
        '''
        self.alert(self.last_alert)
    
    
    def run(self, saver, preredrawer, postredrawer):
        '''
        Execute text reading
        
        @param  saver:()→void         Save method
        @param  preredrawer:()→void   Method to call before redrawing screen
        @param  postredrawer:()→void  Method to call after redaring screen
        '''
        
        self.status('unmodified')
        
        modified = False
        override = False
        
        oldy, oldx, oldmark = self.y, self.x, self.mark
        stored = ctrl('L')
        edited = False
        
        while True:
            if ((oldmark is not None) and (oldmark >= 0)) or ((self.mark is not None) and (self.mark >= 0)):
                self.lines[self.y].draw()
            if self.y != oldy:
                self.lines[oldy].draw()
                self.lines[self.y].draw()
                jump(self.top + self.y, self.left + self.innerleft + self.x - self.offx)()
            (oldy, oldx, oldmark) = (self.y, self.x, self.mark)
            if edited:
                edited = False
                if not modified:
                    modified = True
                    self.status('modified' + (' override' if override else ''))
            sys.stdout.flush()
            if stored is None:
                d = sys.stdin.read(1)
            else:
                d = stored
                stored = None
            if self.alerted:
                self.alert(None)
            if d == ctrl('@'):
                if self.mark is None:
                    self.mark = self.x
                    self.alert('Mark set')
                elif self.mark == ~(self.x):
                    self.mark = self.x
                    self.alert('Mark activated')
                elif self.mark == self.x:
                    self.mark = ~(self.x)
                    self.alert('Mark deactivated')
                else:
                    self.mark = self.x
                    self.alert('Mark set')
            elif d == ctrl('K'):
                if not self.lines[self.y].kill():
                    self.alert('At end')
                else:
                    edited = True
            elif d == ctrl('W'):
                if not self.lines[self.y].cut():
                    self.alert('No text is selected')
                else:
                    edited = True
            elif d == ctrl('Y'):
                if not self.lines[self.y].yank():
                    self.alert('Killring is empty')
                else:
                    edited = True
            elif d == ctrl('X'):
                self.alert('C-x')
                sys.stdout.flush()
                d = sys.stdin.read(1)
                self.alert(str(ord(d)))
                sys.stdout.flush()
                if d == ctrl('X'):
                    if self.lines[self.y].swap_mark():
                        self.alert('Mark swapped')
                    else:
                        self.alert('No mark is activated')
                elif d == ctrl('S'):
                    last = ''
                    for row in range(0, len(self.lines)):
                        self.datamap[self.lines[row].name] = self.lines[row].text
                    saver()
                    modified = False
                    self.status('unmodified' + (' override' if override else ''))
                    self.alert('Saved')
                elif d == ctrl('C'):
                    break
                else:
                    stored = d
                    self.alert(None)
            elif (ord(d) == 127) or (ord(d) == 8):
                if not self.lines[self.y].erase():
                    self.alert('At beginning')
            elif ord(d) < ord(' '):
                if d == ctrl('P'):
                    if self.y == 0:
                        self.alert('At first line')
                    else:
                        self.y -= 1
                        self.mark = None
                        self.x = 0
                elif d == ctrl('N'):
                    if self.y < len(self.lines) - 1:
                        self.y += 1
                        self.mark = None
                        self.x = 0
                    else:
                        self.alert('At last line')
                elif d == ctrl('F'):
                    if not self.lines[self.y].move_point(1):
                        self.alert('At end')
                elif d == ctrl('E'):
                    if not self.lines[self.y].move_point(len(self.lines[self.y].text) - self.x):
                        self.alert('At end')
                elif d == ctrl('B'):
                    if not self.lines[self.y].move_point(-1):
                        self.alert('At beginning')
                elif d == ctrl('A'):
                    if not self.lines[self.y].move_point(-self.x):
                        self.alert('At beginning')
                elif d == ctrl('L'):
                    print('\033[H\033[2J', end='')
                    preredrawer()
                    for line in self.lines:
                        line.draw()
                    postredrawer()
                    self.realert()
                    self.restatus()
                elif d == ctrl('D'):
                    if not self.lines[self.y].delete():
                        self.alert('At end')
                    else:
                        edited = True
                elif d == '\033':
                    d = sys.stdin.read(1)
                    if d == '[':
                        d = sys.stdin.read(1)
                        if d == 'A':
                            stored = ctrl('P')
                        elif d == 'B':
                            if self.y == len(self.lines) - 1:
                                self.alert('At last line')
                            else:
                                stored = ctrl('N')
                        elif d == 'C':
                            stored = ctrl('F')
                        elif d == 'D':
                            stored = ctrl('B')
                        elif d == '2':
                            d = sys.stdin.read(1)
                            if d == '~':
                                override = not override
                                self.status(('modified' if modified else 'unmodified') + (' override' if override else ''))
                        elif d == '3':
                            d = sys.stdin.read(1)
                            if d == '~':
                                stored = ctrl('D')
                        elif d == '1':
                            d = sys.stdin.read(1)
                            if d == '~':
                                stored = ctrl('A')
                        elif d == '4':
                            d = sys.stdin.read(1)
                            if d == '~':
                                stored = ctrl('E')
                        else:
                            while True:
                                d = sys.stdin.read(1)
                                if ord('a') <= ord(d) <= ord('z'): break
                                if ord('A') <= ord(d) <= ord('Z'): break
                                if d == '~': break
                    elif d == 'O':
                        d = sys.stdin.read(1)
                        if d == 'H':
                            stored = ctrl('A')
                        elif d == 'F':
                            stored = ctrl('E')
                    elif (d == 'w') or (d == 'W'):
                        if not self.lines[self.y].copy():
                            self.alert('No text is selected')
                    elif (d == 'y') or (d == 'Y'):
                        if not self.lines[self.y].yank_cycle():
                            stored = ctrl('Y')
                elif d == '\n':
                    stored = ctrl('N')
            else:
                insert = d
                if len(insert) == 0:
                    continue
                if override:
                    self.lines[self.y].override(insert)
                else:
                    self.lines[self.y].insert(insert)
                edited = True


def phonysaver():
    pass
def phonypreredraw():
    pass
def phonypostredraw():
    pass
print('\033[H\033[2J')
old_stty = Popen('stty --save'.split(' '), stdout = PIPE).communicate()[0]
old_stty = old_stty.decode('utf-8', 'error')[:-1]
Popen('stty -icanon -echo -isig -ixon -ixoff'.split(' '), stdout = PIPE).communicate()
try:
    TextArea(['alpha', 'beta'], {'alpha' : 'a', 'beta' : 'be'}, 1, 1, 20, 4).run(phonysaver, phonypreredraw, phonypostredraw)
finally:
    print('\033[H\033[2J', end = '')
    sys.stdout.flush()
    Popen(['stty', old_stty], stdout = PIPE).communicate()

