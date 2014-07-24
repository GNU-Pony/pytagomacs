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
from common import *


class Line():
    '''
    A line in the text area
    '''
    
    def __init__(self, area, name, text, y):
        '''
        Constructor
        
        @param  area:TextArea  The text area
        @param  name:str       The name of the, displayed at the left side
        @param  text:str       The text in the line
        @param  y:int          The y position of the line
        
        '''
        self.area, self.name, self.text, self.y = area, name, text, y
        self.killring = self.area.killring
        self.jump = lambda x : Jump(self.area.top + self.y - self.area.offy, self.area.left + self.area.innerleft + x)
    
    
    def is_active(self):
        '''
        Checks if the line is the focused line
        
        @return  :bool  Whether the line is the focused line
        '''
        return self.area.y == self.y
    
    
    def has_selection(self):
        '''
        Checks if there is any text selected, assuming the line is focused
        
        @param  :bool  Whether there is any text selected
        '''
        return atleast(self.area.mark, 0) and (self.area.mark != self.area.x)
    
    
    def draw(self):
        '''
        Redraw the line
        '''
        if 0 <= self.y - self.area.offy < self.area.height - 2:
            leftside = ACTIVE_COLOUR if self.is_active() else INACTIVE_COLOUR
            if leftside is not None:
                leftside = '%s\033[%sm%s:\033[00m' % (self.jump(-(self.area.innerleft)), leftside, self.name)
            else:
                leftside = '%s%s:' % (self.jump(-(self.area.innerleft)), self.name)
            text = (self.text[self.area.offx if self.is_active() else 0:] + ' ' * self.area.areawidth)[:self.area.areawidth]
            if self.is_active() and atleast(self.area.mark, 0):
                (a, b) = self.area.get_selection(True)
                if a != b:
                    if SELECTED_COLOUR is not None:
                        text = text[:a] + ('\033[%sm%s\033[00m' % (SELECTED_COLOUR, text[a : b])) + text[b:]
            print('%s%s%s' % (leftside, self.jump(0), text), end='')
            if self.is_active():
                self.jump(self.area.x - self.area.offx)()
    
    
    def copy(self):
        '''
        Copy the selected text
        
        @return  :bool  Whether any text select, and therefore copied
        '''
        if self.has_selection():
            (a, b) = self.area.get_selection()
            self.killring.add(self.text[a : b])
            self.killring.reset()
            (a, b) = self.area.get_selection(True)
            text = self.text[self.area.offx:][:self.area.areawidth][a : b]
            print('%s%s' % (self.jump(a), text), end='')
            self.area.mark = None
            return True
        return False
    
    
    def cut(self):
        '''
        Cut the selected text
        
        @return  :bool  Whether any text select, and therefore cut
        '''
        mark, x = self.area.mark, self.area.x
        if self.copy():
            self.area.mark, self.area.x = mark, x
            self.delete()
            return True
        return False
    
    
    def kill(self):
        '''
        Cut all text on the same line after the position of the point
        
        @return  :bool  Whether the point was not at the end of the line, and therefore a cut was made
        '''
        if self.area.x < len(self.text):
            self.area.mark = len(self.text)
            self.cut()
            return True
        return False
    
    
    def delete(self):
        '''
        Delete the selected text or, if none, the character at the position of the point
        
        @return  :bool  The point was not at the end of the line or something was selected, and therefore a deletion was made
        '''
        removed = 0
        if self.has_selection():
            (a, b) = self.area.get_selection()
            self.text = self.text[:a] + self.text[b:]
            self.area.x = a
            if self.area.offx > len(self.text):
                self.area.offx = max(len(self.text) - self.area.areawidth, 0)
                self.area.mark = None
                print('%s%s' % (self.jump(0), ' ' * self.area.areawidth), end='')
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
        print('%s%s%s' % (self.jump(a), text[a:] + ' ' * removed, self.jump(a)), end='')
        return True
    
    
    def erase(self):
        '''
        Select the selected text or the character directly before the position of the point
        
        @return  :bool  Whether point as at the beginning of the line or any text was selected, and therefore an erasure was made
        '''
        if not self.has_selection():
            self.area.mark = None
            if self.area.x == 0:
                return False
            self.area.x -= 1
            if self.area.x < self.area.offx:
                self.area.offx = max(self.area.offx - self.area.areawidth, 0)
                self.draw()
                self.jump(self.area.x - self.area.offx)()
        self.delete()
        return True
    
    
    def yank(self):
        '''
        Yank the text from the top of the killring
        
        @return  :bool  Whether the killring was not empty, and therefor a yank was made
        '''
        if self.killring.is_empty():
            return False
        self.area.mark = None
        yanked = self.killring.get()
        self.text = self.text[:self.area.x] + yanked + self.text[self.area.x:]
        self.area.x += len(yanked)
        if self.area.x > self.area.offx + self.area.areawidth:
            self.area.offx = len(self.text) - self.area.areawidth
        print('%s%s' % (self.jump(0), ' ' * self.area.areawidth), end='')
        self.draw()
        self.jump(self.area.x - self.area.offx)()
        return True
    
    
    def yank_cycle(self):
        '''
        Replace the recently yank text with the next in the killring
        
        @return  :bool  False on failure, which happens if the killring is empty or if the text before the point is not the yanked text
        '''
        if self.killring.is_empty():
            return False
        yanked = self.killring.get()
        if self.text[max(self.area.x - len(yanked), 0) : self.area.x] != yanked:
            return False
        self.area.mark = self.area.x - len(yanked)
        self.delete()
        self.killring.next()
        self.yank()
        return True
    
    
    def move_point(self, delta):
        '''
        Move the the point
        
        @param   delta:int  The number of steps to move the point to the right
        @return  :bool      Whether the point has been moved
        '''
        x = self.area.x + delta
        if 0 <= x <= len(self.text):
            self.area.x = x
            if delta < 0:
                if self.area.offx > self.area.x:
                    self.area.offx = max(self.area.x - 3 * self.area.areawidth // 4, 0)
                    self.draw()
                else:
                    print('\033[%iD' % -delta, end='')
            elif delta > 0:
                if self.area.x - self.area.offx > self.area.areawidth:
                    self.area.offx = self.area.x - self.area.areawidth // 4
                    self.draw()
                else:
                    print('\033[%iC' % delta, end='')
            return delta != 0
        return False
    
    
    def swap_mark(self):
        '''
        Swap the position of the mark and the position of the point
        
        @return  :bool  Whether the mark was set, and therefore as swap was made
        '''
        if atleast(self.area.mark, 0):
            self.area.mark, self.area.x = self.area.x, self.area.mark
            return True
        return False
    
    
    def override(self, insert, override = True):
        '''
        Insert a text (by default) by overriding the existing text at the position of the point
        
        @param  insert:str     The text to insert
        @param  override:bool  Whether to override
        '''
        if atleast(self.area.mark, 0):
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
                print('%s\033[%iP' % (self.jump(self.area.areawidth - len(insert)), len(insert)), end='')
                print('%s\033[%i@' % (self.jump(oldx - self.area.offx), len(insert)), end='')
            print(insert, end='')
        else:
            self.area.offx = self.area.x - self.area.areawidth // 4
            self.jump(0)()
            print(' ' * self.area.areawidth, end='')
            self.draw()
    
    
    def insert(self, insert):
        '''
        Insert a text at the position of the point
        
        @param  insert:str  The text to insert
        '''
        self.override(insert, False)

