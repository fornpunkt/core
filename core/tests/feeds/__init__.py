from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning, UserDetails


class GeoRSSTest(TestCase):
    '''Tests of the GeoRSS feed'''

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='31(21)2HJHJ')
        cls.user.save()

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=cls.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

        lamning = Lamning.objects.create(
            title='Testlämning 2',
            description='Testlämning 2',
            geojson='{"type":"Feature","geometry":{"type":"LineString","coordinates":[[17.000246506461547,58.73422091201479],[17.000272914559705,58.73434974847828],[17.000278196179337,58.73449777276221]]},"properties":null}',
            observation_type='FO',
            user=cls.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

        lamning = Lamning.objects.create(
            title='Testlämning 3',
            description='Testlämning 3',
            geojson='{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-25.136719,38.134557],[5.625,54.775346],[49.746094,34.307144],[4.746094,23.079732],[-25.136719,38.134557]]]}}',
            observation_type='FO',
            user=cls.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

    def test_feed(self):
        '''Tests that the GeoRSS feed is generated correctly'''
        response = self.client.get(reverse('tag_rss', kwargs={'slug': 'testtagg'}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/rss+xml' in response.headers['Content-Type'])

        self.assertContains(response, '<georss:point>60.5963 13.0743</georss:point>')
        self.assertContains(response, '<georss:line>58.734221 17.000247 58.73435 17.000273 58.734498 17.000278</georss:line>')
        self.assertContains(response, '<georss:polygon>38.134557 -25.136719 54.775346 5.625 34.307144 49.746094 23.079732 4.746094 38.134557 -25.136719</georss:polygon>')

class UserFeedAccessTest(TestCase):
    '''Checks that only users whos profiles have public feeds'''

    @classmethod
    def setUpTestData(cls):
        cls.members_only_user = User.objects.create_user(username='jskdk', password='31(21)2HJHJ')
        cls.members_only_user.save()
        members_only_user_details = UserDetails.objects.get(user=cls.members_only_user)
        members_only_user_details.profile_privacy = 'ME'
        members_only_user_details.save()

        cls.public_user = User.objects.create_user(username='ksdsgdgh', password='31(21)2HJHJ')
        cls.public_user.save()
        public_user_details = UserDetails.objects.get(user=cls.public_user)
        public_user_details.profile_privacy = 'PU'
        public_user_details.save()

        # private profile should be the default so no need to update UserDetails
        cls.private_user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.private_user.save()

        cls.inactive_user = User.objects.create_user(username='banned', password='hjhj', is_active=False)
        cls.inactive_user.save()

    def test_members_only_is_not_public(self):
        '''Tests that the members only user is not public'''
        response = self.client.get(reverse('user_lamnings_rss', kwargs={'slug': 'jskdk'}))
        self.assertEqual(response.status_code, 403)

    def test_public_is_public(self):
        '''Tests that the public user is public'''
        response = self.client.get(reverse('user_lamnings_rss', kwargs={'slug': 'ksdsgdgh'}))
        self.assertEqual(response.status_code, 200)

    def test_private_is_not_public(self):
        '''Tests that the private user is not public'''
        response = self.client.get(reverse('user_lamnings_rss', kwargs={'slug': 'test'}))
        self.assertEqual(response.status_code, 403)

    def test_inactive_is_not_public(self):
        '''Tests that the inactive user is not public'''
        response = self.client.get(reverse('user_lamnings_rss', kwargs={'slug': 'banned'}))
        self.assertEqual(response.status_code, 403)
