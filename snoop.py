# -*- coding: utf-8 -*-
#
#	   Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'


import logging
import codecs
import re
import time
import json
import os
import pyte
import errno


class Sniffer(object):
    """
    Captures session IO to files
    """

    def __init__(self, user, src_port, host, uuid, screen_size):
        self.user = user
        self.host = host
        self.uuid = uuid
        self.src_port = src_port
        self.log_file = None
        self.log_timer = None
        self.log_cmds = None
        self.session_start_time = time.strftime("%H%M%S")
        self.session_start_date = time.strftime("%Y%m%d")
        self.session_date_time = time.strftime("%Y/%m/%d %H:%M:%S")
        self.today = time.strftime("%Y%m%d")
        self.session_log = "{0}_{1}_{2}_{3}".format(
            self.user, self.host.name, self.session_start_time, self.uuid)
        self.stream = None
        self.screen = None
        self.term_cols, self.term_rows = screen_size
        self._fake_terminal()
        logging.debug("Sniffer: Sniffer Created")

    def _fake_terminal(self):
        logging.debug(
            "Sniffer: Creating Pyte screen with cols %i and rows %i" %
            (self.term_cols, self.term_rows))
        self.screen = pyte.Screen(self.term_cols, self.term_rows)
        self.stream = pyte.ByteStream()
        self.stream.attach(self.screen)

    def extract_command(self, buf):
        """
        Handle terminal escape sequences
        """
        command = ""
        # Remove CR (\x0D) in middle of data
        # probably will need better handling
        # See https://github.com/selectel/pyte/issues/66
        logging.debug("buf b4 is %s" % str(buf))
        buf = buf.replace('\x0D', '')
        logging.debug("buf after is %s" % buf)
        try:
            self.stream.feed(buf)
            output = "".join(
                [l for l in self.screen.display if len(l.strip()) > 0]).strip()
            # for line in reversed(self.screen.buffer):
            #output = "".join(map(operator.attrgetter("data"), line)).strip()
            logging.debug("output is %s" % output)
            command = self.ps1_parser(output)
        except Exception as e:
            logging.error(
                "Sniffer: extract command error {0} ".format(
                    e.message))
            pass
        self.screen.reset()
        return command

    def ps1_parser(self, command):
        """
        Extract commands from PS1 or mysql>
        """
        result = None
        match = re.compile('\[?.*@.*\]?[\$#]\s').split(command)
        logging.debug("Sniffer: command match is %s" % match)
        if match:
            result = match[-1].strip()
        else:
            # No PS1, try finding mysql
            match = re.split('mysql>\s', command)
            logging.debug("Sniffer: command match is %s" % match)
            if match:
                result = match[-1].strip()
        return result

    @staticmethod
    def got_cr_lf(string):
        newline_chars = ['\n', '\r', '\r\n']
        for char in newline_chars:
            if char in string:
                return True
        return False

    @staticmethod
    def findlast(s, substrs):
        i = -1
        result = None
        for substr in substrs:
            pos = s.rfind(substr)
            if pos > i:
                i = pos
                result = substr
        return result

    def set_logs(self):
        # local import
        from aker import session_log_dir
        today_sessions_dir = os.path.join(
            session_log_dir, self.session_start_date)
        log_file_path = os.path.join(today_sessions_dir, self.session_log)
        try:
            os.makedirs(today_sessions_dir, 0o777)
            os.chmod(today_sessions_dir, 0o777)
        except OSError as e:
            if e.errno != errno.EEXIST:
                logging.error(
                    "Sniffer: set_logs OS Error {0} ".format(
                        e.message))
        try:
            log_file = open(log_file_path + '.log', 'a')
            log_timer = open(log_file_path + '.timer', 'a')
            log_cmds = log_file_path + '.cmds'
        except IOError:
            logging.debug("Sniffer: set_logs IO error {0} ".format(e.message))

        log_file.write('Session Start %s\r\n' % self.session_date_time)
        self.log_file = log_file
        self.log_timer = log_timer
        self.log_cmds = log_cmds

    def stop(self):
        session_end = time.strftime("%Y/%m/%d %H:%M:%S")
        # Sayonara
        jsonmsg = {'ver': '1',
                   'host': self.host,
                   'user': self.user,
                   'session': str(self.uuid),
                   'sessionstart': self.session_date_time,
                   'sessionend': session_end,
                   'timing': session_end,
                   }

        try:
            with open(self.log_cmds, 'a') as outfile:
                jsonout = json.dumps(jsonmsg)
                outfile.write(jsonout + '\n')
        except Exception as e:
            logging.error(
                "Sniffer: close session files error {0} ".format(
                    e.message))

        try:
            self.log_file.write('Session End %s' % session_end)
            self.log_file.close()
            self.log_timer.close()
        except:
            logging.debug("Sniffer: Failed to close files. Likely due to a session close before establishing.")


class SSHSniffer(Sniffer):
    def __init__(self, user, src_port, host, uuid, screen_size):
        super(
            SSHSniffer,
            self).__init__(
            user,
            src_port,
            host,
            uuid,
            screen_size)
        self.vim_regex = re.compile(r'\x1b\[\?1049', re.X)
        self.vim_data = ""
        self.stdin_active = False
        self.in_alt_mode = False
        self.buf = ""
        self.vim_data = ""
        self.before_timestamp = time.time()
        self.start_timestamp = self.before_timestamp
        self.start_alt_mode = set(['\x1b[?47h', '\x1b[?1049h', '\x1b[?1047h'])
        self.end_alt_mode = set(['\x1b[?47l', '\x1b[?1049l', '\x1b[?1047l'])
        self.alt_mode_flags = tuple(
            self.start_alt_mode) + tuple(self.end_alt_mode)

    def channel_filter(self, x):
        now_timestamp = time.time()
        # Write delta time and number of chrs to timer log
        self.log_timer.write(
            '%s %s\n' %
            (round(
                now_timestamp -
                self.before_timestamp,
                4),
                len(x)))
        self.log_timer.flush()
        self.log_file.write(x)
        self.log_file.flush()
        self.before_timestamp = now_timestamp
        self.vim_data += x
        # Accumlate data when in stdin_active
        if self.stdin_active:
            self.buf += x

    def stdin_filter(self, x):
        self.stdin_active = True
        flag = self.findlast(self.vim_data, self.alt_mode_flags)
        if flag is not None:
            if flag in self.start_alt_mode:
                logging.debug("In ALT mode")
                self.in_alt_mode = True
            elif flag in self.end_alt_mode:
                logging.debug("Out of ALT mode")
                self.in_alt_mode = False
        # We got CR/LF?
        if self.got_cr_lf(str(x)):
            if not self.in_alt_mode:
                logging.debug("Sniffer: self.buf is : %s" % self.buf)

                # Did x capture the last character and CR ?
                if len(str(x)) > 1:
                    self.buf = self.buf + x
                logging.debug("Sniffer: x is : %s" % x)

                self.buf = self.extract_command(self.buf)

                # If we got something back, log it
                if self.buf is not None and self.buf != "":
                    now = time.strftime("%Y/%m/%d %H:%M:%S")
                    # TODO: add a separate object for json later
                    jsonmsg = {
                        'ver': '1',
                        'host': self.host,
                        'user': self.user,
                        'session': str(
                            self.uuid),
                        'sessionstart': self.session_date_time,
                        'timing': now,
                        'cmd': codecs.decode(
                            self.buf,
                            'UTF-8',
                            "replace")}
                    try:
                        with open(self.log_cmds, 'a') as outfile:
                            # ELK's filebeat require a jsonlines like file
                            # (http://jsonlines.org/)
                            jsonout = json.dumps(jsonmsg)
                            outfile.write(jsonout + '\n')
                    except Exception as e:
                        logging.error(
                            "Sniffer: stdin_filter error {0} ".format(
                                e.message))
                    jsonmsg = {}

            self.buf = ""
            self.vim_data = ""
            self.stdin_active = False

    def sigwinch(self, columns, lines):
        logging.debug(
            "Sniffer: Setting Pyte screen size to cols %i and rows %i" %
            (columns, lines))
        self.screen.resize(columns, lines)
