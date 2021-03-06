﻿# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'


def strQ2B(ustring):
    """把字符串全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 0x3000:
            inside_code = 0x20
        elif 0xFF01 <= inside_code <= 0xFF5E:
            inside_code -= 0xfee0
        rstring += chr(inside_code)
    return rstring


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def confirm(prompt=None, resp=False):
    """
    From: http://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/
    prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print('please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False


def select(options, prompt=None):
    if prompt is None:
        prompt = 'select'
    prompt += ':\n'
    for i, o in enumerate(options):
        prompt += '%d) %s%s\n' % (i, o, '*' if i ==0 else '')
    while True:
        ans = input(prompt)
        if not ans:
            return 0
        if not ans.isdigit() or not (0 <= int(ans) < len(options)):
            print('please enter valid selection')
            print(int(ans))
            continue
        return int(ans)