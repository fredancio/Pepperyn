"""Local falsification only; does not certify a live authenticated reread."""
import unittest
from unittest.mock import patch
import httpx
from fastapi import HTTPException
from sandbox.read_completed_b1 import build_app, PATH, COMPANY


class WindowTests(unittest.IsolatedAsyncioTestCase):
    async def probe(self, method='GET', path=PATH, *, company=COMPANY, kind='admin',
                    host='127.0.0.1', expired=False, missing=False, receipt=True):
        async def auth(authorization, auth_type):
            if missing:
                raise HTTPException(401)
            return company, 'free', kind
        app = build_app(object(), auth, deadline=10, clock=lambda: 11 if expired else 1)
        output = {'execution_provenance': {'status': 'VERIFIED_RECEIPT' if receipt else 'UNATTESTED'}}
        with patch('sandbox.read_completed_b1.read_owned_output', return_value=output) as reader:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(host, 99)), base_url='http://local') as client:
                response = await client.request(method, path)
                if response.status_code == 200:
                    self.assertEqual(response.headers['cache-control'], 'no-store')
                    self.assertEqual((await client.get(PATH)).status_code, 403)
                return response.status_code, reader.call_count

    async def test_owned_read_and_single_success(self):
        self.assertEqual(await self.probe(), (200, 1))

    async def test_denied_boundaries(self):
        for options in ({'method':'POST'}, {'path':PATH+'/export.pdf'}, {'path':PATH+'x'},
                        {'path':PATH+'?company_id=other'}, {'host':'192.0.2.1'}, {'expired':True}):
            with self.subTest(options=options):
                self.assertEqual(await self.probe(**options), (403, 0))

    async def test_authentication_and_ownership(self):
        self.assertEqual(await self.probe(missing=True), (401, 0))
        self.assertEqual(await self.probe(company='foreign'), (404, 0))
        self.assertEqual(await self.probe(kind='guest'), (404, 0))

    async def test_unattested_refused(self):
        self.assertEqual(await self.probe(receipt=False), (503, 1))


if __name__ == '__main__':
    unittest.main()
