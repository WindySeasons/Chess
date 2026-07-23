import urllib.request
import os, time

# GitHub release 直链
URL = 'https://github.com/official-pikafish/Pikafish/releases/download/Pikafish-2026-01-02/Pikafish.2026-01-02.7z'
OUT = r'c:\D\个人项目\Chess\pikafish.7z'

for i in range(3):
    try:
        print(f'Attempt {i+1}/3: Downloading Pikafish...')
        urllib.request.urlretrieve(URL, OUT)
        size = os.path.getsize(OUT)
        if size < 10000:
            raise Exception(f'Too small: {size} bytes')
        print(f'Success! {size} bytes')
        break
    except Exception as e:
        print(f'Failed: {e}')
        if i < 2:
            print('Retrying in 5s...')
            time.sleep(5)
else:
    print('All attempts failed.')
