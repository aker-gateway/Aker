# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from pyte import ByteStream,Screen,modes as mo


if __name__ == "__main__":
    screen = Screen(80, 24)
#    screen.reset_mode(mo.LNM)
    stream = ByteStream()
    stream.attach(screen)
    stream.feed(b"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDQqBdvF4pLXmnjoTEXtoMEykpDHfmEtxZUiWepT0kUMIQ8E7NRzNJKMN/EiZP+HX/u6\x0D61bDHXQbbbGcQ/vsaTNGLBvbWa3KcW7sS4LmmK/frbI24fI+DoeTzxOOocT0UFKRrOwRAJtpRZWRC6iGto7w7hvwdJUszO2v+orbl4W9Soikzxge4EXI0xkLw\x0DwWP2vfqFgxZEM0wcuZE2XLDBp8KzDDhju6wn97XltPOTxKRjVWdl5Iibc5SInVSdAAEouIE/2xPKwUfPFIYh6Cg2OcrXfRJ101Ttn1PbtJiFY7k8UPNUcH7Ni\x0Di5+vZzXjzjkFEha+3D5rjvOjZMPZpS4kMqZl anazmy@rhlaptop\x0D
\x0D
\x0D
\x0D\x03
0;anazmy@db1:~\x07[anazmy@db1 ~]$ history -d $((HISTCMD-1)) && sudo lvs")

    for idx, line in enumerate(screen.display, 1):
        print("{0:2d} {1} ¶".format(idx, line))
