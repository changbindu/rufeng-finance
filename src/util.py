# coding=utf-8
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
