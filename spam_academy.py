#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2009 Reto Schüttel <reto -ät- schuettel dot ch>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import pwd
import time
import subprocess
import logging as log
from mailbox import Maildir
from email.Generator import Generator
from tempfile import NamedTemporaryFile, TemporaryFile

log.basicConfig(level=log.DEBUG)

KEEP_ENV = ['PATH', 'SHELL', 'HOME', 'USER']
def change_to_user(user):
  uid, gid = pwd.getpwnam(user)[2:4]

  os.setgid(gid)
  os.setuid(uid)
  os.setegid(gid)
  os.seteuid(uid)

  # strip unwanted env variables
  for key in os.environ.keys():
    if key not in KEEP_ENV:
      del os.environ[key]

  # set new env vars:
  os.environ['USER'] = user
  os.environ['HOME'] = path


HOME = "/home/"
FLAG = ".spam_academy"
FOLDER_OPEN = "offen"
FOLDER_LEARNED = "gelernt"
# FOLDER_OPEN = "todo"
# FOLDER_LEARNED = "done"

for user in os.listdir(HOME):
  path = HOME + "/" + user

  if not os.path.exists(path + "/" + FLAG):
    log.debug("Skip %s" % user)
    continue

  pid = os.fork()

  if pid != 0:
    (pid_c, status) = os.waitpid(pid, 0)
    ret = status >> 8
    log.debug("child returned with status %i" % ret)

    if ret != 0:
      log.critical("child returned with error, aborting!")
      sys.exit(ret)

    continue

  try:
    change_to_user(user)

    maildir_path = path + "/.maildir/"

    if not os.path.exists(maildir_path):
      log.warn("%s doesn't have a maildir" % user)
      sys.exit(0)

    maildir = Maildir(maildir_path, factory=None)

    spam_open    = maildir.add_folder('SA.Spam.' + FOLDER_OPEN)
    spam_learend = maildir.add_folder('SA.Spam.' + FOLDER_LEARNED)
    ham_open     = maildir.add_folder('SA.Ham.'  + FOLDER_OPEN)
    ham_learned  = maildir.add_folder('SA.Ham.'  + FOLDER_LEARNED)

    jobs = (
      ('spam', ('spamassassin', '-r', '-D' ), spam_open, spam_learend),
      ('ham',  ('sa-learn', '--ham', '-D' ), ham_open, ham_learned)
    )


    for desc, cmd, mbox_todo, mbox_done in jobs:
      log.info  ("User %s: processing %s" % (user, desc))

      for key, msg in mbox_todo.items():
        # store mail in a temporary file
        mail = NamedTemporaryFile()
        g = Generator(mail, mangle_from_=False, maxheaderlen=0)
        g.flatten(msg)

        mail.flush()
        mail.seek(0)

        # move the mail to the learned folder
        mbox_done.add(msg)
        mbox_todo.discard(key)

        std_out = NamedTemporaryFile()
        std_err = NamedTemporaryFile()


        start = time.time()
        p = subprocess.Popen(cmd, stdin=mail, stdout=std_out, stderr=std_out, cwd=path)

        ret = p.wait()
        duration = time.time() - start

        log.debug("User %s: cmd: %s ret: %i duration: %i msg: %s" % (user, str(cmd), ret, duration, key))

        std_out.flush()
        std_err.flush()

        log_dir = path + "/.sa/log/" + key
        os.makedirs(log_dir)
        mail_log   = file(log_dir + "/mail.log", "w")
        stdout_log = file(log_dir + "/stdout.log", "w")
        stderr_log = file(log_dir + "/stderr.log", "w")

        std_out.seek(0)
        std_err.seek(0)
        mail.seek(0)
        mail_log.write(mail.read())
        stdout_log.write(std_out.read())
        stderr_log.write(std_err.read())

        for fh in std_err, std_out, mail, mail_log, stdout_log, stderr_log:
          fh.close()

    # end children here
  except:
    log.exception("Error during child run for %s" % user)
    raise
  sys.exit(0)






