import os
import subprocess
from common.basedir import BASEDIR

env = os.environ.copy()
env['SCONS_CACHE'] = "1"

nproc = os.cpu_count()
j_flag = '-j16'
scons = subprocess.Popen(["scons", j_flag], cwd=BASEDIR, env=env)
