from datetime import datetime
import subprocess
import re

env_map={'TEST':'herp','ME':'derp','PLEASE':'hi'}
# One capture group of the environment variable
BASIC_RE = r'\$(\w+|\{[^}]*\})'
# 3 groups: 1 full capture, 2 variable name, 3 prefix value
PREFIX_RE = r'(\${(\w+)\/#\/(.+)})'

def environment_expansion(env_map, cmd_string):
    # inject environment and perform env replacement in string
    output = subprocess.check_output(["bash","-c","echo \"{}\"".format(cmd_string)], env=env_map)

    # Remove the trailing new line returned by bash
    return output.rstrip('\n')

def environment_echo(env_map, cmd_string):
    # inject environment and perform env replacement in string
    output = subprocess.check_output(["echo \"{}\"".format(cmd_string)], env=env_map, shell=True)

    # Remove the trailing new line returned by bash
    return output.rstrip('\n')



def environment_pure(env_map, cmd_string):
    # inject environment and perform env replacement in string
    def dict_lookup(match):
	prefix = None
        key = match.group(1)
        key = key.lstrip('{').rstrip('}')
	if '/#/' in key:
	    key,sep,prefix = key.split('/')
        if key in env_map:
	    value = env_map[key]
	    if prefix:
		value = prefix + value
            return value
        return ''

    first_pass = re.sub(BASIC_RE, dict_lookup, cmd_string)
    second_pass = re.sub(PREFIX_RE, dict_lookup, first_pass)   
    return second_pass

start = datetime.now()
for i in range(1000):
     print(environment_pure(env_map,'oh $TEST ${ME} ${PLEASE/#/-p } ${NOTHING}'))
     print(environment_pure(env_map,'oh $TEST ${ME} ${PLEASE/#/-p } ${NOTHING} ${Invalid $TEST-hi'))
duration = datetime.now() - start
print('Pure python expansion took: %s', duration)

start = datetime.now()
for i in range(1000):
     print(environment_expansion(env_map,'oh $TEST ${ME} ${PLEASE/#/-p } ${NOTHING}'))
duration = datetime.now() - start
print('Bash based expansion took: %s', duration)

start = datetime.now()
for i in range(1000):
     environment_echo(env_map,'oh $TEST $ME')
duration = datetime.now() - start
print('Pure echo expansion took: %s', duration)

