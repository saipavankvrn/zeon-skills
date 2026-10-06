import unittest
from werkzeug.security import check_password_hash
from app import app, db, User, Skill, Category, UserSkillAttempt

class ZeonSkillsTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        self._cleanup_test_data()

    def tearDown(self):
        self._cleanup_test_data()
        self.app_context.pop()

    def _cleanup_test_data(self):
        # Keep the seed user saipavankvrn@zeon.com intact, remove test-generated users
        User.query.filter(User.email != 'saipavankvrn@zeon.com').delete(synchronize_session=False)
        db.session.commit()

    def test_01_unauthenticated_access_restrictions(self):
        """Unauthenticated users should be redirected to login for protected routes"""
        protected_routes = [
            '/home',
            '/profile',
            '/popularquiz',
            '/quizview',
            '/viewresult',
            '/admin_dashboard',
            '/admin_createskill',
            '/admin_allskill',
            '/admin_categories'
        ]
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=False)
            self.assertEqual(response.status_code, 302, f"Expected 302 redirect for {route}, got {response.status_code}")
            self.assertIn('/', response.headers['Location'], f"Expected redirect to login ('/'), got {response.headers['Location']}")

    def test_02_legacy_user_login_and_hash_migration(self):
        """Existing user with plain text password should log in successfully and have password migrated to hash"""
        user = User.query.filter_by(email='saipavankvrn@zeon.com').first()
        self.assertIsNotNone(user, "User saipavankvrn@zeon.com should exist in database")

        response = self.client.post('/', data={
            'username': 'saipavankvrn@zeon.com',
            'password': '12345'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/home', response.headers['Location'])

        # Check DB to verify password hash migration
        db.session.refresh(user)
        self.assertTrue(user.password.startswith(('scrypt:', 'pbkdf2:')), "Password should now be hashed")
        self.assertTrue(check_password_hash(user.password, '12345'), "Hashed password should verify against '12345'")

    def test_03_registration_with_secure_hashing(self):
        """New registration should require valid password, hash it, and prevent duplicate emails"""
        # Short password rejected
        res = self.client.post('/registration', data={
            'name': 'Short Pwd User',
            'email': 'short@example.com',
            'password': '123'
        }, follow_redirects=True)
        self.assertIn(b'Password must be at least 6 characters long', res.data)

        # Valid registration
        res = self.client.post('/registration', data={
            'name': 'Alice Candidate',
            'email': 'alice@example.com',
            'password': 'SecurePassword123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)

        # Check database
        new_u = User.query.filter_by(email='alice@example.com').first()
        self.assertIsNotNone(new_u)
        self.assertEqual(new_u.name, 'Alice Candidate')
        self.assertEqual(new_u.role, 'user')
        self.assertTrue(new_u.password.startswith(('scrypt:', 'pbkdf2:')))
        self.assertTrue(check_password_hash(new_u.password, 'SecurePassword123'))

        # Duplicate email rejected
        res_dup = self.client.post('/registration', data={
            'name': 'Duplicate Alice',
            'email': 'alice@example.com',
            'password': 'AnotherPassword123'
        }, follow_redirects=True)
        self.assertIn(b'Email already registered', res_dup.data)

    def test_04_profile_view_and_editing(self):
        """Logged-in user can view profile without exposed password, and edit name/email safely"""
        # Register and login Alice
        self.client.post('/registration', data={
            'name': 'Alice Candidate',
            'email': 'alice@example.com',
            'password': 'SecurePassword123'
        })
        self.client.post('/', data={'username': 'alice@example.com', 'password': 'SecurePassword123'})

        # View Profile
        res = self.client.get('/profile')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Alice Candidate', res.data)
        self.assertIn(b'alice@example.com', res.data)
        self.assertIn(b'Candidate / User', res.data)
        self.assertNotIn(b'SecurePassword123', res.data)

        # Update Name and Email
        res_post = self.client.post('/profile', data={
            'name': 'Alice Updated',
            'email': 'alice.updated@example.com',
            'role': 'admin' # Malicious attempt to escalate role
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn(b'Profile updated successfully!', res_post.data)

        # Verify DB
        alice_db = User.query.filter_by(email='alice.updated@example.com').first()
        self.assertIsNotNone(alice_db)
        self.assertEqual(alice_db.name, 'Alice Updated')
        self.assertEqual(alice_db.role, 'user', "User role MUST NOT be changed to admin by user profile submission")

    def test_05_change_password_flow(self):
        """User can change password securely with validation"""
        # Register and login Carol
        self.client.post('/registration', data={
            'name': 'Carol Test',
            'email': 'carol@example.com',
            'password': 'SecurePassword123'
        })
        self.client.post('/', data={'username': 'carol@example.com', 'password': 'SecurePassword123'})

        # Wrong current password
        res = self.client.post('/change-password', data={
            'current_password': 'WrongPassword!',
            'new_password': 'BrandNewPassword123',
            'confirm_password': 'BrandNewPassword123'
        }, follow_redirects=True)
        self.assertIn(b'Current password is incorrect', res.data)

        # Mismatch
        res = self.client.post('/change-password', data={
            'current_password': 'SecurePassword123',
            'new_password': 'BrandNewPassword123',
            'confirm_password': 'DifferentPassword123'
        }, follow_redirects=True)
        self.assertIn(b'New password and confirm password do not match', res.data)

        # Short new password
        res = self.client.post('/change-password', data={
            'current_password': 'SecurePassword123',
            'new_password': '123',
            'confirm_password': '123'
        }, follow_redirects=True)
        self.assertIn(b'New password must be at least 6 characters long', res.data)

        # Valid password change
        res = self.client.post('/change-password', data={
            'current_password': 'SecurePassword123',
            'new_password': 'BrandNewPassword123',
            'confirm_password': 'BrandNewPassword123'
        }, follow_redirects=True)
        self.assertIn(b'Password changed successfully!', res.data)

        # Logout and test login with old password fails
        self.client.get('/logout')
        res_old = self.client.post('/', data={'username': 'carol@example.com', 'password': 'SecurePassword123'}, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res_old.data)

        # Login with new password succeeds
        res_new = self.client.post('/', data={'username': 'carol@example.com', 'password': 'BrandNewPassword123'}, follow_redirects=False)
        self.assertEqual(res_new.status_code, 302)
        self.assertIn('/home', res_new.headers['Location'])

    def test_06_logout_flow_and_session_clearing(self):
        """Logout should clear the session completely and prevent authenticated access"""
        self.client.post('/registration', data={
            'name': 'David Test',
            'email': 'david@example.com',
            'password': 'Password123'
        })
        self.client.post('/', data={'username': 'david@example.com', 'password': 'Password123'})
        res_home = self.client.get('/home')
        self.assertEqual(res_home.status_code, 200)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(res_logout.status_code, 302)
        self.assertIn('/', res_logout.headers['Location'])

        # Now /home and /profile must redirect to login
        res_after = self.client.get('/home', follow_redirects=False)
        self.assertEqual(res_after.status_code, 302)
        res_prof = self.client.get('/profile', follow_redirects=False)
        self.assertEqual(res_prof.status_code, 302)

    def test_07_admin_and_user_separation(self):
        """Normal users cannot access admin pages; admin users can access admin pages and profile"""
        # Register normal user
        self.client.post('/registration', data={
            'name': 'Eve User',
            'email': 'eve@example.com',
            'password': 'EvePassword123'
        })
        # Register an admin account (email with @zeonskills.com)
        self.client.post('/registration', data={
            'name': 'Site Admin',
            'email': 'admin@zeonskills.com',
            'password': 'AdminPassword123'
        })
        admin_u = User.query.filter_by(email='admin@zeonskills.com').first()
        self.assertIsNotNone(admin_u)
        self.assertEqual(admin_u.role, 'admin')

        # Normal user attempts to access admin dashboard
        self.client.post('/', data={'username': 'eve@example.com', 'password': 'EvePassword123'})
        res_admin = self.client.get('/admin_dashboard', follow_redirects=False)
        self.assertEqual(res_admin.status_code, 302)
        self.assertIn('/', res_admin.headers['Location'])

        # Normal user attempts add_category API
        res_cat = self.client.post('/add_category', json={'name': 'UnauthorizedCategory'}, follow_redirects=False)
        self.assertEqual(res_cat.status_code, 403)

        # Logout user
        self.client.get('/logout')

        # Admin logs in
        res_login_admin = self.client.post('/', data={'username': 'admin@zeonskills.com', 'password': 'AdminPassword123'}, follow_redirects=False)
        self.assertEqual(res_login_admin.status_code, 302)
        self.assertIn('/admin_dashboard', res_login_admin.headers['Location'])

        # Admin accesses admin dashboard
        res_dash = self.client.get('/admin_dashboard')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b'Site Admin', res_dash.data)

        # Admin accesses profile
        res_admin_prof = self.client.get('/profile')
        self.assertEqual(res_admin_prof.status_code, 200)
        self.assertIn(b'Administrator', res_admin_prof.data)

        # Admin adds category
        res_cat_ok = self.client.post('/add_category', json={'name': 'Cloud Computing'})
        self.assertEqual(res_cat_ok.status_code, 200)
        self.assertTrue(res_cat_ok.get_json()['success'])

    def test_08_navbar_and_sections_on_home(self):
        """Home page navbar contains all items, anchor targets exist, and no dead href='#' in nav"""
        # Login persistent user
        self.client.post('/', data={'username': 'saipavankvrn@zeon.com', 'password': '12345'})
        res = self.client.get('/home')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Check navbar items
        self.assertIn('Home</a>', html)
        self.assertIn('About</a>', html)
        self.assertIn('How It Works</a>', html)
        self.assertIn('Why Choose Us</a>', html)
        self.assertIn('Popular Quiz</a>', html)
        self.assertIn('Testimonials</a>', html)
        self.assertIn('href="/profile"', html)
        self.assertIn('href="/logout"', html)
        self.assertIn('Profile', html)
        self.assertIn('Logout', html)

        # Check section IDs exist on page
        self.assertIn('id="home"', html)
        self.assertIn('id="about"', html)
        self.assertIn('id="how-it-works"', html)
        self.assertIn('id="why-choose-us"', html)
        self.assertIn('id="popular-quiz"', html)
        self.assertIn('id="testimonials"', html)
        self.assertIn('id="contact"', html)

if __name__ == '__main__':
    unittest.main()
