import os
import subprocess
from common.basedir import BASEDIR

env = os.environ.copy()
env['SCONS_CACHE'] = "1"

nproc = os.cpu_count()
j_flag = "" if nproc is None else "-j%d" % (nproc - 1)
scons = subprocess.Popen(["scons", j_flag], cwd=BASEDIR, env=env, stderr=subprocess.PIPE)
