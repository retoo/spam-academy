#!/usr/bin/python

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


LOG_DIR = "/var/tmp/log-sa"
HOME = "test"
FLAG = ".spamcademy"

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
    continue

  change_to_user(user)


  maildir_path = path + "/.maildir/"

  if not os.path.exists(maildir_path):
    log.warn("%s doesn't have a maildir" % user)
    sys.exit(0)

  maildir = Maildir(maildir_path, factory=None)

  if "SA" not in maildir.list_folders():
    log.info("Creating structure for user %s" % user)
    # create initial structure
    sa = maildir.add_folder("SA")
    spam = sa.add_folder("Spam")
    ham  = sa.add_folder("Ham")

    for d in spam, ham:
      d.add_folder("offen")
      d.add_folder("gelernt")

  sa = maildir.add_folder("SA")
  spam_open    = sa.get_folder('Spam').get_folder('offen')
  spam_learend = sa.get_folder('Spam').get_folder('gelernt')

  ham_open     = sa.get_folder('Ham').get_folder('offen')
  ham_learned  = sa.get_folder('Ham').get_folder('gelernt')


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

      mail_log   = file(LOG_DIR + "/" + key + "_mail.log", "w")
      stdout_log = file(LOG_DIR + "/" + key + "_stdout.log", "w")
      stderr_log = file(LOG_DIR + "/" + key + "_stderr.log", "w")

      std_out.seek(0)
      std_err.seek(0)
      mail.seek(0)
      mail_log.write(mail.read())
      stdout_log.write(std_out.read())
      stderr_log.write(std_err.read())

      for fh in std_err, std_out, mail, mail_log, stdout_log, stderr_log:
        fh.close()

      sys.exit(0)
  # end children here
  sys.exit(0)






