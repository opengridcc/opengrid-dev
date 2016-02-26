import os
import tmpo
print(tmpo.__file__)

tmpo1 = tmpo.Session(os.getcwd())
tmpo1.add('key', 'token')
tmpo2 = tmpo.Session(os.getcwd())
tmpo2.add('key', 'token')

print("Test successful")