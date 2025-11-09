import time
import requests


def req():
    session = requests.Session()
# '{"cookies": {"sessioncookie": "123456789"}}'
    for job in range(3140+1):
        print(job)
        r = session.get(f'http://localhost:8000/{job}', params = {'src': 'sync'})
        print(r.text)

def main():
    t1 = time.perf_counter()
    req()
    print(f'Completed by {(time.perf_counter() - t1)/60} minute(s)')
    
main()    