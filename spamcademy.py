#!/usr/bin/python2.5

import sys
import os
import pwd
import logging as log
from mailbox import Maildir

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

  maildir = Maildir(maildir_path)

  if "SA" not in maildir.list_folders():
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

  #for id, msg in spam_open.items():
  #  print id, msg

  # end children here
  sys.exit(0)






