import urllib.request, urllib.parse, json, uuid, time
from urllib.error import HTTPError

BASE = 'http://localhost:8000'
email = f'test_{uuid.uuid4().hex[:6]}@demo.com'
password = 'TestPassword123!'

print('1. Registering user...')
req = urllib.request.Request(BASE+'/api/v1/auth/register', data=json.dumps({'email':email,'password':password}).encode(), headers={'Content-Type':'application/json'}, method='POST')
res = urllib.request.urlopen(req)
print('   -> OK:', json.loads(res.read())['email'])

print('2. Logging in...')
req = urllib.request.Request(BASE+'/api/v1/auth/login', data=urllib.parse.urlencode({'username':email,'password':password}).encode(), headers={'Content-Type':'application/x-www-form-urlencoded'}, method='POST')
res = urllib.request.urlopen(req)
token = json.loads(res.read())['access_token']
print('   -> OK: Token received')

print('3. Uploading a valid minimal PNG image...')
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    b'--' + boundary.encode() + b'\r\n' +
    b'Content-Disposition: form-data; name="file"; filename="test_exam.png"\r\n' +
    b'Content-Type: image/png\r\n\r\n' +
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\x99c\xf8\x0f\x04\x00\x09\xfb\x03\xfd\xe3U\xf2\x9c\x00\x00\x00\x00IEND\xaeB`\x82' + b'\r\n' +
    b'--' + boundary.encode() + b'--\r\n'
)

req = urllib.request.Request(BASE+'/api/v1/documents/upload', data=body, headers={'Content-Type':f'multipart/form-data; boundary={boundary}', 'Authorization': f'Bearer {token}'}, method='POST')
try:
    res = urllib.request.urlopen(req)
    doc_data = json.loads(res.read())
    doc_id = doc_data['id']
    print('   -> OK: Uploaded doc_id', doc_id)
except HTTPError as e:
    print('   -> Upload Failed:', e.code, e.read().decode())
    doc_id = None

if doc_id:
    print('4. Polling status (Testing graceful synchronous fallback without Celery)...')
    for _ in range(5):
        time.sleep(1)
        req = urllib.request.Request(BASE+f'/api/v1/documents/{doc_id}/status', headers={'Authorization': f'Bearer {token}'})
        status_data = json.loads(urllib.request.urlopen(req).read())
        print('   -> Status:', status_data['status'])
        if status_data['status'] in ('completed', 'failed'):
            if status_data['status'] == 'failed':
                print('   -> Reason:', status_data.get('error_message'))
            break
