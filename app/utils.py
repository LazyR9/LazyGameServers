import shlex

def get_cmd(cmd: str, replacements):
   return shlex.split(cmd.format_map(replacements))