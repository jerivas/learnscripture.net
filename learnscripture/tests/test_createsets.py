import time

from awards.models import AwardType
from bibleverses.models import StageType, VerseSet, VerseSetType
from events.models import Event, EventType

from .base import FullBrowserTest


class CreateSetTests(FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(CreateSetTests, self).setUp()
        self._identity, self._account = self.create_account()

    def _add_ref(self, ref):
        self.fill({"#id_quick_find": ref})
        self.click("#id_lookup")
        self.click("input.add-to-set")
        self.wait_until_loaded('#id-verse-list tbody tr td')
        time.sleep(0.1)

    def test_create_selection_set(self):
        self.login(self._account)
        self.get_url('create_selection_set')
        self.fill({"#id_name": "My set",
                   "#id_description": "My description"})
        self._add_ref("Gen 1:5")
        self.assertTextPresent("And God called the light Day")

        self.fill({"#id_public": True})
        self.submit("#id-save-btn")
        self.assertTrue(self.get_page_title().startswith("Verse set: My set"))
        self.assertTextPresent("And God called the light Day")

        self.assertEqual(self._account.awards.filter(award_type=AwardType.SHARER).count(),
                         1)
        self.assertEqual(Event.objects.filter(event_type=EventType.VERSE_SET_CREATED).count(),
                         1)

    def test_dedupe_selection_sets(self):
        self.login(self._account)
        self.get_url("create_selection_set")
        self.fill({"#id_name": "My set"})

        # Add Gen 1:5
        self._add_ref("Genesis 1:5")

        self.click("#id-save-btn")

        vs = VerseSet.objects.get(name='My set')
        self.assertEqual(len(vs.verse_choices.all()), 1)

        current_ref_list = [("Genesis 1:5", 0)]

        def _add_new_ref(ref):
            # Edit again
            self.get_url('edit_set', slug=vs.slug)
            self._add_ref(ref)

            self.click("#id-save-btn")

            self.assertTextPresent("Verse set 'My set' saved")  # Checks we didn't get 500

            if ref not in [r for r, i in current_ref_list]:
                current_ref_list.append((ref, len(current_ref_list)))

            self.assertEqual(current_ref_list,
                             sorted([(vc.reference, vc.set_order)
                                     for vc in vs.verse_choices.all()]))

        # Caching could cause these to fail
        _add_new_ref("Genesis 1:6")
        _add_new_ref("Genesis 1:6")
        _add_new_ref("Genesis 1:7")
        _add_new_ref("Genesis 1:7")

    def test_forget_name(self):
        """
        If they forget the name, it should not validate,
        but shouldn't forget the verse list
        """
        self.login(self._account)
        self.get_url('create_selection_set')

        self._add_ref("Gen 1:5")
        self._add_ref("Gen 1:6")

        self.submit("#id-save-btn")

        self.assertTrue(self.get_page_title().startswith("Create selection set"))
        self.assertTextPresent("This field is required")
        self.assertTextPresent("Genesis 1:5")
        self.assertTextPresent("Genesis 1:6")

    def test_edit(self):
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.SELECTION,
                                     name='my set')
        vc1 = vs.verse_choices.create(reference='Genesis 1:1',
                                      set_order=0)
        vc2 = vs.verse_choices.create(reference='Genesis 1:5',
                                      set_order=1)
        vc3 = vs.verse_choices.create(reference='Genesis 1:10',
                                      set_order=2)
        self.login(self._account)
        self.get_url('edit_set', slug=vs.slug)
        self.drag_and_drop_by_offset("#id-verse-list tbody tr:first-child td",
                                     0, 60)
        self.submit("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc1.id, vc2.id, vc3.id]))
        self.assertEqual(vs.verse_choices.get(reference='Genesis 1:1').set_order, 1)
        self.assertEqual(vs.verse_choices.get(reference='Genesis 1:5').set_order, 0)

    def test_remove(self):
        self.login(self._account)
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.SELECTION,
                                     name='my set')
        vs.verse_choices.create(reference='Genesis 1:1',
                                set_order=0)
        vc2 = vs.verse_choices.create(reference='Genesis 1:5',
                                      set_order=1)

        identity = self._identity
        # Record some learning against the verse we will remove
        identity.add_verse_set(vs)
        identity.record_verse_action('Genesis 1:1', 'KJV', StageType.TEST, 1.0)

        self.get_url('edit_set', slug=vs.slug)
        self.click("#id-verse-list tbody tr:first-child td .icon-trash")
        self.click("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual([vc.id for vc in vcs], [vc2.id])

        # Need to ensure that the UVS has not been deleted
        identity.verse_statuses.get(version__slug='KJV', reference='Genesis 1:1')

    def test_require_account(self):
        self.get_url('create_selection_set')
        self.set_preferences()
        self.assertTextPresent('You need to')
        self.assertTextPresent('create an account')

    def test_create_passage_set(self):
        self.login(self._account)
        self.get_url('create_passage_set')

        self.fill({"#id_name": "Genesis 1:1-10"})
        self.fill({"#id_description": "My description"})

        self.fill({"#id_quick_find": "Gen 1:1-10"})
        self.click("#id_lookup")
        self.wait_until_loaded('#id-verse-list tbody tr td')
        self.assertTextPresent("And God called the light Day")

        # Check boxes for Genesis 1:3, 1:9
        self.click('#id-verse-list tbody tr:nth-child(3) input')
        self.click('#id-verse-list tbody tr:nth-child(9) input')

        self.click("#id-save-btn")
        self.assertTrue(self.get_page_title().startswith("Verse set: Genesis 1"))
        self.assertTextPresent("And God called the light Day")

        vs = VerseSet.objects.get(name='Genesis 1:1-10',
                                  set_type=VerseSetType.PASSAGE)
        self.assertTrue(len(vs.verse_choices.all()), 10)
        self.assertEqual(vs.breaks, "1:3,1:9")
        self.assertEqual(vs.passage_id, 'Genesis 1:1 - Genesis 1:10')

    def test_create_duplicate_passage_set(self):
        self.test_create_passage_set()
        self.get_url("create_passage_set")
        self.fill({"#id_quick_find": "Gen 1:1-10"})

        self.click("#id_lookup")
        self.wait_until_loaded('#id-verse-list tbody tr td')
        self.assertTextPresent("There are already")

    def test_empty_passage_set(self):
        self.login(self._account)
        self.get_url("create_passage_set")
        self.fill({"#id_name": "xxx"})
        self.click("#id-save-btn")
        self.assertTextPresent("No verses in set")

    def test_edit_passage_set(self):
        self.login(self._account)
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.PASSAGE,
                                     name='Psalm 23',
                                     breaks="23:5")
        references = []
        for i in range(1, 7):
            ref = 'Psalm 23:%d' % i
            references.append(ref)
            vs.verse_choices.create(reference=ref,
                                    set_order=i - 1)

        # Simple test - editing and pressing save should leave
        # everything the same.
        self.get_url('edit_set', slug=vs.slug)
        self.click("#id-save-btn")

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all().order_by('set_order')
        self.assertEqual([vc.reference for vc in vcs],
                         references)
        self.assertEqual(vs.breaks, "23:5")
