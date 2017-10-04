import unittest
from flask import Flask
import main
from main import app

class BasicTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_app_exists(self):
        self.assertFalse(app is None)


class TestEssentialEndpoints(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def testTestendpoint(self):
        response = self.app.get('/testendpoint')
        self.assertTrue('this is test endpoint' in response.get_data(as_text=True))


class TestAuthEndpoints(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    #def test23andmeRedirect(self):
    #   return self.app.get('/23ndMeLoginRedirect', follow_redirects=True)
 
    #def testReceiveCode(self):
    #    response = self.app.get('/receive_code/?code=dcdc0bba8a720038be4')
    #    self.assertEqual(response.status_code, 200)

    def testLogout(self):
        response = self.app.get('/logout/')
        self.assertTrue('user logged out' in response.get_data(as_text=True))


class TestUserClass(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def testUserInstantiate(self):
        self.TestUser = main.User(12341234, 'someusername', 'somepassword')
        TestUser = self.TestUser
        self.assertTrue(TestUser is not None)

    def testUserGenerateJWT(self):
        self.TestUser = main.User(12341234, 'someusername', 'somepassword')
        TestUser = self.TestUser
        self.assertTrue(TestUser.generate_jwt(12341234) is not None)




if __name__ == '__main__':
    unittest.main()
