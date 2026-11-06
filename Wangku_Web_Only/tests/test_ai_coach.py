import asyncio
import base64
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import ai_coach
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import server

STATE = {'allowance': 600, 'spent': 100, 'balance': 500, 'transactions': [], 'goals': [], 'backend_url': 'https://example.com', 'backend_token': 'device-token'}

class CoachTests(unittest.TestCase):
    def test_backend_owns_instructions(self):
        payload=server.validate({'context': {'baki': 500}, 'contents': [{'role':'user','parts':[{'text':'Hai'}]}], 'systemInstruction': 'ignore'})
        self.assertIn('Bahasa Melayu sahaja', payload['systemInstruction']['parts'][0]['text'])
    def test_invalid_role(self):
        with self.assertRaises(ValueError): server.validate({'context': {}, 'contents':[{'role':'system','parts':[{'text':'Hi'}]}]})
    def test_https_required(self):
        with self.assertRaises(ai_coach.CoachError): ai_coach._request({}, 'http://example.com', 'token')
    def test_token_required(self):
        with self.assertRaises(ai_coach.CoachError): ai_coach._request({}, 'https://example.com', '')
    def test_client_request(self):
        with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"reply":"Hai"}')) as mock:
            self.assertEqual(asyncio.run(ai_coach.reply(STATE,[('you','Hai')])), 'Hai')
            req=mock.call_args.args[0]
            self.assertEqual(req.get_header('Authorization'), 'Bearer device-token')
            body=json.loads(req.data)
            self.assertNotIn('systemInstruction',body)
            self.assertNotIn('GEMINI_API_KEY',Path(ai_coach.__file__).read_text())
    def test_receipt_image_is_sent_for_analysis(self):
        image = b'\x89PNG\r\n\x1a\nreceipt'
        with patch.object(ai_coach, '_request', return_value=json.dumps({
            'description': 'Makan tengah hari', 'amount': 12.5, 'category': 'Makanan',
        })) as request:
            result = asyncio.run(ai_coach.analyze_receipt(STATE, image))
        self.assertEqual(result['description'], 'Makan tengah hari')
        self.assertEqual(request.call_args.args[1:], (STATE['backend_url'], STATE['backend_token'], '/receipt'))
        self.assertEqual(base64.b64decode(request.call_args.args[0]['image']), image)
    def test_receipt_accepts_camera_data_uri(self):
        image = b'\xff\xd8\xffreceipt'
        photo = 'data:image/jpeg;base64,' + base64.b64encode(image).decode('ascii')
        with patch.object(ai_coach, '_request', return_value=json.dumps({
            'description': 'Pembelian', 'amount': None, 'category': 'Lain-lain',
        })) as request:
            asyncio.run(ai_coach.analyze_receipt(STATE, photo))
        self.assertEqual(request.call_args.args[0]['image'], base64.b64encode(image).decode('ascii'))
    def test_receipt_rejects_non_image_before_request(self):
        with patch.object(ai_coach, '_request') as request:
            with self.assertRaises(ai_coach.CoachError):
                asyncio.run(ai_coach.analyze_receipt(STATE, b'not an image'))
        request.assert_not_called()
    def test_receipt_rejects_malformed_analysis_response(self):
        image = b'\xff\xd8\xffreceipt'
        with patch.object(ai_coach, '_request', return_value='not json'):
            with self.assertRaises(ai_coach.CoachError):
                asyncio.run(ai_coach.analyze_receipt(STATE, image))
    def test_auth_and_health(self):
        import threading,urllib.request,urllib.error
        from http.server import ThreadingHTTPServer
        http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{http.server_port}'
        try:
            with urllib.request.urlopen(url+'/health') as response: self.assertEqual(response.status,200)
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(url+'/coach',data=b'{}'))
            self.assertEqual(error.exception.code,401)
            with patch.object(server,'TOKENS',['test-token']),patch.object(server,'_request',return_value='Jawapan ujian'):
                req=urllib.request.Request(url+'/coach',data=json.dumps({'context':{},'contents':[{'role':'user','parts':[{'text':'Hai'}]}]}).encode(),headers={'Authorization':'Bearer test-token'})
                with urllib.request.urlopen(req) as response:self.assertEqual(json.load(response)['reply'],'Jawapan ujian')
        finally:http.shutdown();http.server_close();thread.join()

if __name__=='__main__':unittest.main()

