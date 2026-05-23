import subprocess
import sys

# Run migration with 'N' answer
process = subprocess.Popen(
    [sys.executable, 'manage.py', 'migrate', 'accounts'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Answer 'N' to the rename question
stdout, stderr = process.communicate(input='N\n')

print(stdout)
if stderr:
    print(stderr, file=sys.stderr)

sys.exit(process.returncode)
