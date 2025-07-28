import re
import subprocess
import yaml

def log_analyzer(): 
    count = 0
    with open('check.log') as f, open('debugger.log','w') as wf:
        prev = 0
        for idx, line in enumerate(f,start =1 ):
            mat = re.search(r'ID: (?P<loop_id>\d+), JobID: (?P<job_id>\d+)',line)
            if (loop_id:=int(mat.group('loop_id'))) == (job_id:=int(mat.group('job_id'))):
                if prev!=0 and (prev + 1 == loop_id):
                    wf.write(f'line_no = {idx}, {loop_id = }, {job_id = }, {prev = }, is_same = true\n')
                    count += 1
                prev = loop_id
    return f'{count/10_000:.2%}'

buffer_sizes =  [2,5,10,15,20,25,30,40]
dct = {}
for idx, buffer_size in enumerate(buffer_sizes, start = 1):
    print(f'{buffer_size = }')
    subprocess.run(f"go run . {buffer_size}".split())
    consecutoveness = log_analyzer()
    time = open('duration.txt').read().strip()
    dct[f'TEST_{idx}'] = {
        'jobs': 10000,
        'workers': 500,
        'buffer_size': buffer_size,
        'consecutoveness': consecutoveness,
        'time': time
    }

with open(f'metrics/worker_500.yaml','w') as f:
    yaml.safe_dump(dct, f)



