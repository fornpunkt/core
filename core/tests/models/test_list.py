from django.test import TestCase

from ...models import Lamning, List, ShadowLamning, User


class ListModelTest(TestCase):
    '''Tests the List model'''

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.user.save()

        cls.lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=cls.user
        )
        cls.lamning.save()

        cls.shadow_lamning = ShadowLamning.objects.create(
            uuid='550e8400-e29b-41d4-a716-446655440000',
            title='Test RAA Lamning',
            description='Test description',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            lamning_type='Grav'
        )
        cls.shadow_lamning.save()

        cls.list = List.objects.create(
            title='Test Lista',
            description='En testlista',
            user=cls.user,
            hidden=False
        )
        cls.list.lamnings.add(cls.lamning)
        cls.list.shadow_lamnings.add(cls.shadow_lamning)
        cls.list.save()

    def test_list_creation(self):
        '''Smoke test for list creation'''
        list_obj = List.objects.get(id=self.list.id)
        self.assertEqual(list_obj.title, 'Test Lista')
        self.assertEqual(list_obj.description, 'En testlista')
        self.assertEqual(list_obj.user, self.user)
        self.assertFalse(list_obj.hidden)

    def test_list_many_to_many(self):
        '''Test that M2M relationships work'''
        list_obj = List.objects.get(id=self.list.id)
        self.assertEqual(list_obj.lamnings.count(), 1)
        self.assertEqual(list_obj.shadow_lamnings.count(), 1)
        self.assertEqual(list_obj.total_items(), 2)

    def test_list_hashid(self):
        '''Test that hashid is generated'''
        list_obj = List.objects.get(id=self.list.id)
        self.assertIsNotNone(list_obj.hashid)
        self.assertGreater(len(list_obj.hashid), 0)

    def test_list_get_absolute_url(self):
        '''Test get_absolute_url'''
        list_obj = List.objects.get(id=self.list.id)
        url = list_obj.get_absolute_url()
        self.assertIn('/lista/', url)

    def test_list_json_ld(self):
        '''Test JSON-LD generation'''
        list_obj = List.objects.get(id=self.list.id)
        json_ld = list_obj.json_ld
        self.assertEqual(json_ld['@type'], 'schema:Collection')
        self.assertEqual(json_ld['schema:name'], 'Test Lista')
        self.assertIn('schema:itemListElement', json_ld)
        self.assertEqual(len(json_ld['schema:itemListElement']), 2)


class ShadowLamningModelTest(TestCase):
    '''Tests the ShadowLamning model'''

    @classmethod
    def setUpTestData(cls):
        cls.shadow_lamning = ShadowLamning.objects.create(
            uuid='550e8400-e29b-41d4-a716-446655440000',
            title='Test RAA Lamning',
            description='Test description',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            lamning_type='Grav',
            center_lat=60.5963,
            center_lon=13.0743
        )
        cls.shadow_lamning.save()

    def test_shadow_lamning_creation(self):
        '''Smoke test for shadow lamning creation'''
        shadow = ShadowLamning.objects.get(uuid='550e8400-e29b-41d4-a716-446655440000')
        self.assertEqual(shadow.title, 'Test RAA Lamning')
        self.assertEqual(shadow.lamning_type, 'Grav')

    def test_shadow_lamning_json_ld(self):
        '''Test JSON-LD generation'''
        shadow = ShadowLamning.objects.get(uuid='550e8400-e29b-41d4-a716-446655440000')
        json_ld = shadow.json_ld
        self.assertEqual(json_ld['@type'], 'schema:CreativeWork')
        self.assertIn('550e8400-e29b-41d4-a716-446655440000', json_ld['@id'])

    def test_shadow_lamning_verbose_geojson(self):
        '''Test verbose_geojson generation'''
        shadow = ShadowLamning.objects.get(uuid='550e8400-e29b-41d4-a716-446655440000')
        geojson = shadow.verbose_geojson
        self.assertIsNotNone(geojson)
        self.assertEqual(geojson['properties']['title'], 'Test RAA Lamning')
        self.assertEqual(geojson['properties']['type'], 'Grav')
