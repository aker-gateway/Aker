# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
import logging
import os
from Queue import Queue
import stat
import threading
import sys


class Sniffer(object):
    def __init__(self):
        self.original_stdout = sys.stdout
        self.log_filename = None
        self._keys_queue = Queue()
        logging.debug("Sniffer: Base Sniffer Created")

    def fileno(self):
        return self.original_stdout.fileno()

    def set_log_filename(self, log_filename):
        self.log_filename = log_filename

    def write(self, c):
        self._keys_queue.put(c)
        self.original_stdout.write(c.decode(self.original_stdout.encoding))

    def read(self, fd):
        data = os.read(fd, 1024)
        self._keys_queue.put(data)
        return data

    def flush(self):
        self.original_stdout.flush()

    def capture(self):
        if self.log_filename:
            sys.stdout = self
            self._sniffer = SessionSniffer(self._keys_queue)
            self._sniffer.set_log_filename(self.log_filename)
            self._sniffer.start()

    def restore(self):
        if self.log_filename:
            sys.stdout = self.original_stdout
            self._sniffer.stop()
            self._sniffer.join()
            self.log_filename = None


class SessionSniffer(threading.Thread):
    def __init__(self, keys_queue):
        threading.Thread.__init__(self)
        self._key_queue = keys_queue
        self._log_file = None
        self._session_stop = False
        logging.debug("Sniffer: SessionSniffer Created")

    def set_log_filename(self, log_filename):
        self._log_filename = log_filename

    def run(self):
        if self._log_filename:
            self._log_file = open(self._log_filename, "wb")
            os.chmod(self._log_file.name,
                     stat.S_IREAD |
                     stat.S_IWRITE |
                     stat.S_IWRITE |
                     stat.S_IRGRP |
                     stat.S_IROTH)
        while True:
            if not self._session_stop:
                c = self._key_queue.get()
                self.write_input(c)
                self._key_queue.task_done()
            else:
                if self._log_filename:
                    self._log_file.close()
                logging.debug("Sniffer: Stop")
                break

    def stop(self):
        self._session_stop = True
        self._key_queue.put("")

    def write_input(self, c):
        if self._log_file:
            self._log_file.write(c)
            self._log_file.flush()
            os.fsync(self._log_file.fileno())
