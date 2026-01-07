#!/usr/bin/env python3
import requests

def check_tapo_p115():
    try:
        response = requests.get('http://localhost:7777/api/sensors/tapo-p115', timeout=5)
        print(f'Tapo P115 API status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Plug count: {data.get("count", 0)}')
            if data.get('count', 0) > 0:
                print('Plugs found:')
                for plug in data.get('devices', []):
                    print(f'  - {plug.get("name")}: {plug.get("current_power", 0)}W')
            else:
                print('No plugs found')
        else:
            print(f'Error: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

def check_cameras():
    try:
        response = requests.get('http://localhost:7777/api/cameras', timeout=5)
        print(f'Cameras API status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Camera count: {data.get("count", 0)}')
            if data.get('count', 0) > 0:
                print('Cameras found:')
                for camera in data.get('cameras', []):
                    print(f'  - {camera.get("name")}: {camera.get("status", "unknown")}')
            else:
                print('No cameras found')
        else:
            print(f'Error: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    print("Checking Tapo P115 plugs...")
    check_tapo_p115()
    print("\nChecking cameras...")
    check_cameras()