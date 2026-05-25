import subprocess
import sys

# Run makemigrations with 'n' as input
process = subprocess.Popen(
    [sys.executable, 'backend/manage.py', 'makemigrations'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send 'n' to answer the rename question
stdout, stderr = process.communicate(input='n\n')

print(stdout)
if stderr:
    print(stderr, file=sys.stderr)

sys.exit(process.returncode)
