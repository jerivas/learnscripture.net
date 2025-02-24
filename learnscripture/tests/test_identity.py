from datetime import timedelta

from django.db.models import F
from django.utils import timezone
from django_ftl import override
from time_machine import travel

import accounts.memorymodel
from accounts.models import ChosenVerseSet
from awards.models import AwardType
from bibleverses.languages import LANG
from bibleverses.models import (
    MemoryStage,
    StageType,
    TextVersion,
    Verse,
    VerseChoice,
    VerseSet,
    VerseSetType,
    WordSuggestionData,
)
from bibleverses.parsing import internalize_localized_reference
from events.models import Event, EventType

from .base import AccountTestMixin, BibleVersesMixin, CatechismsMixin, FuzzyInt, TestBase, get_or_create_any_account
from .test_bibleverses import RequireExampleVerseSetsMixin


class IdentityTests(RequireExampleVerseSetsMixin, AccountTestMixin, CatechismsMixin, BibleVersesMixin, TestBase):

    databases = {"default", "wordsuggestions"}

    def test_add_verse_set(self):
        i = self.create_identity()
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)

        uvss = i.verse_statuses.all()
        assert len(uvss) == len(vs1.verse_choices.all())

        assert {u.localized_reference for u in uvss} == {"John 3:16", "John 14:6", "Ephesians 2:8-9"}

        vs1 = VerseSet.objects.get(name="Bible 101")  # fresh
        # Having already created the UserVerseStatuses, this should be an
        # efficient operation:
        with self.assertNumQueries(FuzzyInt(3, 7)):
            # 1 for existing uvs, same version
            # 1 for other versions.
            # possibly one for verse_choices_all(), depending on caching
            # 1 for VerseSet.popularity update
            # 3 for awards
            uvss = i.add_verse_set(vs1)
            # session.set_verse_statuses will use all these:
            [(uvs.localized_reference, uvs.verse_set_id) for uvs in uvss]

    def test_add_verse_set_copies_existing_data(self):
        i = self.create_identity(version_slug="KJV")
        # First add John 3:16
        i.add_verse_choice("John 3:16")
        i.record_verse_action("John 3:16", "KJV", StageType.TEST, 1)
        uvs_orig = i.verse_statuses.get(localized_reference="John 3:16")

        # Now add verse set as well, which contains John 3:16
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)

        # We should get a new one, because we want it to have a verse_set link
        assert i.verse_statuses.filter(localized_reference="John 3:16").count() == 2

        # The data for new John 3:16 should be copied from the old
        for uvs in i.verse_statuses.filter(localized_reference="John 3:16"):
            for attr in [
                "memory_stage",
                "strength",
                "ignored",
                "added",
                "first_seen",
                "last_tested",
                "next_test_due",
                "early_review_requested",
            ]:
                with self.subTest(attr=attr):
                    assert getattr(uvs, attr) == getattr(uvs_orig, attr)

    def test_add_verse_set_passage_with_merged(self):
        i = self.create_identity(version_slug="TCL02")
        vs = VerseSet.objects.create(
            created_by=get_or_create_any_account(),
            language_code="en",
            set_type=VerseSetType.PASSAGE,
            name="Romans 3:24-27",
        )
        # Romans 3:25-26 is merged in TCL02
        for so, ref in enumerate(["Romans 3:24", "Romans 3:25", "Romans 3:26", "Romans 3:27"]):
            vs.verse_choices.create(internal_reference=internalize_localized_reference(LANG.EN, ref), set_order=so)

        created = i.add_verse_set(vs)
        assert len(created) == 3

        uvss = i.verse_statuses.all().order_by("text_order")
        assert len(uvss) == 3

        assert {u.localized_reference for u in uvss} == {"Romalılar 3:24", "Romalılar 3:25-26", "Romalılar 3:27"}

        assert [u.text_order for u in uvss] == [27003, 27004, 27005]

    def test_record_read(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)

        assert (
            i.verse_statuses.get(localized_reference="John 3:16", version__slug="NET").memory_stage == MemoryStage.ZERO
        )

        i.record_verse_action("John 3:16", "NET", StageType.READ, 1)
        with travel(timezone.now() + timedelta(seconds=10)):

            uvs = i.verse_statuses.get(localized_reference="John 3:16", version__slug="NET")
            assert uvs.memory_stage == MemoryStage.SEEN
            assert uvs.first_seen is not None

            first_seen = uvs.first_seen
            i.record_verse_action("John 3:16", "NET", StageType.READ, 1)
            uvs = i.verse_statuses.get(localized_reference="John 3:16", version__slug="NET")
            # first_seen field should not have changed
            assert uvs.first_seen == first_seen

    def test_add_verse_set_progress_and_choose_again(self):
        """
        Tests that if we choose a verse a second time after making progress with
        it already, the progress is remembered.
        """
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)

        i.record_verse_action("John 3:16", "NET", StageType.READ, 1)

        vs2 = VerseSet.objects.get(name="Basic Gospel")
        i.add_verse_set(vs2)

        assert i.verse_statuses.get(localized_reference="John 3:16", verse_set=vs2).memory_stage == MemoryStage.SEEN

    def test_record_doesnt_decrease_stage(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)
        i.record_verse_action("John 3:16", "NET", StageType.READ, 1)
        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1)
        assert (
            i.verse_statuses.get(localized_reference="John 3:16", version__slug="NET").memory_stage
            == MemoryStage.TESTED
        )

    def test_record_against_verse_in_multiple_sets(self):
        # Setup
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)
        vs2 = VerseSet.objects.get(name="Basic Gospel")
        i.add_verse_set(vs2)

        assert i.verse_statuses.filter(localized_reference="John 3:16").count() == 2
        i.record_verse_action("John 3:16", "NET", StageType.READ, 1)

        # Test
        assert i.verse_statuses.get(localized_reference="John 3:16", verse_set=vs1).memory_stage == MemoryStage.SEEN
        assert i.verse_statuses.get(localized_reference="John 3:16", verse_set=vs2).memory_stage == MemoryStage.SEEN

    def test_record_test_sets_next_due(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)
        i.record_verse_action("John 3:16", "NET", StageType.READ, 1)
        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1)
        next_due = i.verse_statuses.get(localized_reference="John 3:16", version__slug="NET").next_test_due
        # First test - should be set to minimum of 1 hour
        MM = accounts.memorymodel.MM
        now = timezone.now()
        assert now + timedelta(seconds=0.9 * MM.MIN_TIME_BETWEEN_TESTS) < next_due
        assert next_due < now + timedelta(seconds=1.1 * MM.MIN_TIME_BETWEEN_TESTS)

    def test_review_sooner(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)
        i.record_verse_action("John 3:16", "NET", StageType.READ, 1)
        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1)
        gap = timedelta(seconds=1000)
        i.review_sooner("John 3:16", "NET", gap.seconds)
        uvs = i.verse_statuses.get(localized_reference="John 3:16", version__slug="NET")
        assert uvs.next_test_due == uvs.last_tested + gap

        assert i.next_verse_due() == uvs

        with travel(timezone.now() + gap + timedelta(seconds=100)) as tm:

            uvs.refresh_from_db()
            assert uvs.needs_testing_individual

            assert i.first_overdue_verse(timezone.now()) == uvs

            # Something manually selected for review sooner should be
            # reviewed even if strength is 'fully learned'
            i.verse_statuses.update(strength=accounts.memorymodel.LEARNED)
            uvs.refresh_from_db()
            assert i.first_overdue_verse(timezone.now()) == uvs
            assert uvs.needs_testing_individual
            assert uvs.needs_testing

            # If we record a test again, 'early_review_requested' should be reset,
            # so that the overrides of 'review_sooner' no longer take effect. (The
            # user has to keep on requeted 'see sooner' if they want to that verse
            # to keep on being seen after being learned.
            i.record_verse_action("John 3:16", "NET", StageType.TEST, 1)
            uvs.refresh_from_db()
            now = timezone.now()
            assert uvs.next_test_due > now

            # Verse should not be due in the future
            assert i.next_verse_due() is None

            gap2 = uvs.next_test_due - now
            tm.shift(gap2 + timedelta(seconds=100))

            # Verse should not become overdue
            assert i.first_overdue_verse(timezone.now()) is None

    def test_record_creates_awards(self):
        i, account = self.create_account(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)
        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1)
        # Check 'STUDENT'
        assert account.awards.filter(award_type=AwardType.STUDENT, level=1).count() == 1
        # Check 'MASTER'
        # frig the data:
        i.verse_statuses.update(
            strength=accounts.memorymodel.MM.LEARNED - 0.001, last_tested=timezone.now() - timedelta(100)
        )
        # Now do test to move above LEARNED
        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1)
        assert account.awards.filter(award_type=AwardType.MASTER, level=1).count() == 1

    def test_bible_verse_statuses_for_reviewing(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)
        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1.0)

        # It shouldn't be set for reviewing yet
        assert [] == list(i.bible_verse_statuses_for_reviewing())

        # It is confusing if it is ever ready within an hour, so we special case
        # that:
        with travel(timezone.now() + timedelta(hours=0.99)) as tm:
            assert [] == list(i.bible_verse_statuses_for_reviewing())

            # After 1 hour we expect it to be due
            tm.shift(timedelta(hours=0.1))
            assert ["John 3:16"] == [uvs.localized_reference for uvs in i.bible_verse_statuses_for_reviewing()]

    def test_bible_verse_statuses_for_reviewing_urgency(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)
        # Day 1 - start on John 3:16
        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1.0)
        # Day 2 - revise
        with travel(timezone.now() + timedelta(days=1)) as tm:
            i.record_verse_action("John 3:16", "NET", StageType.TEST, 1.0)
            # Day 7 - start on Eph 2:8-9
            tm.shift(timedelta(days=5))
            i.record_verse_action("Ephesians 2:8-9", "NET", StageType.TEST, 1.0)
            # Day 8:
            tm.shift(timedelta(days=1))
            # John 3:16 is now overdue by several days, more in absolute terms than
            # Ephesians 2:8-9. However, the latter is more urgent, because it is
            # very new. So should come first:
            assert ["Ephesians 2:8-9", "John 3:16"] == [
                uvs.localized_reference for uvs in i.bible_verse_statuses_for_reviewing()
            ]

    def test_passages_for_learning(self):
        i = self.create_identity(version_slug="NET")

        with self.assertNumQueries(1):  # Just 1 query when nothing being learned
            i.passages_for_learning()

        vs1 = VerseSet.objects.get(name="Psalm 23")
        i.add_verse_set(vs1)

        with self.assertNumQueries(2):
            i.passages_for_learning()

        i.add_verse_set(vs1, self.KJV)

        i.record_verse_action("Psalm 23:1", "NET", StageType.TEST, 1.0)
        with self.assertNumQueries(2):
            cvss = i.passages_for_learning()
        assert cvss[0].verse_set.id == vs1.id
        assert cvss[0].version.short_name == "NET"
        assert cvss[0].tested_total == 1
        assert cvss[0].untested_total == 5
        assert cvss[0].needs_review_total == 0

        assert cvss[1].verse_set.id == vs1.id
        assert cvss[1].version.short_name == "KJV"
        assert cvss[1].tested_total == 0
        assert cvss[1].untested_total == 6
        assert cvss[1].needs_review_total == 0

        # Put time back so that they ought to be up for review:
        i.verse_statuses.update(last_tested=timezone.now() - timedelta(10), next_test_due=timezone.now() - timedelta(1))

        with self.assertNumQueries(2):
            cvss = i.passages_for_learning()
        assert cvss[0].verse_set.id == vs1.id
        assert cvss[0].version.short_name == "KJV"
        assert cvss[0].needs_review_total == 0

        assert cvss[1].verse_set.id == vs1.id
        assert cvss[1].version.short_name == "NET"
        assert cvss[1].needs_review_total == 1  # Psalm 23:1

        # Shouldn't be in general revision queue -
        # sneak a test for bible_verse_statuses_for_reviewing() here
        assert [] == list(i.bible_verse_statuses_for_reviewing())

    def test_passages_for_reviewing_and_learning(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")
        vs1.breaks = "BOOK18 23:3,BOOK18 23:6"  # break at v3 and v6 to be unsymmetric
        vs1.save()

        i.add_verse_set(vs1)

        with travel(timezone.now()) as tm:
            for vn in range(1, 7):
                ref = "Psalm 23:%d" % vn
                with self.subTest(ref=ref):
                    i.record_verse_action(ref, "NET", StageType.TEST, 1.0)
                    tm.shift(timedelta(days=1))

                    # Now test again, for all but one verse, which means we will only
                    # have one verse that is due for review, but the whole
                    # passage should be considered as needing review.
                    if vn != 1:
                        i.record_verse_action(ref, "NET", StageType.TEST, 1.0)

                    with self.assertNumQueries(FuzzyInt(3, 4)):
                        # 1 for passages_for_learning, 2 for review passages,
                        # or 3 for passages_for_learning, 1 for review passage
                        cvss_review, cvss_learn = i.passages_for_reviewing_and_learning()

                    if vn < 6:
                        # Nothing to review, because one item still remains
                        # to be initially learned.
                        assert cvss_review == []
                        assert cvss_learn[0].verse_set.id == vs1.id
                    else:
                        assert cvss_learn == []
                        cvs = cvss_review[0]
                        assert cvs.verse_set.id == vs1.id
                        assert not cvs.group_testing
                        assert cvs.needs_testing_count == 5
                        assert cvs.total_verse_count == 6

                    # Shouldn't be in general revision queue
                    assert [] == list(i.bible_verse_statuses_for_reviewing())

            # Now test all verses
            for vn in range(1, 7):
                ref = "Psalm 23:%d" % vn
                i.record_verse_action(ref, "NET", StageType.TEST, 1.0)

            # Should have nothing left to review now.
            cvss_review, cvss_learn = i.passages_for_reviewing_and_learning()
            assert cvss_review == []
            assert cvss_learn == []

            # Time passes:
            tm.move_to(i.verse_statuses.order_by("next_test_due").first().next_test_due + timedelta(days=1))
            # and strengths advance a lot: First past group testing limit
            i.verse_statuses.update(strength=accounts.memorymodel.STRENGTH_FOR_GROUP_TESTING + 0.01)
            # Then some but not all past fully learned:
            i.verse_statuses.exclude(localized_reference__in=["Psalm 23:3", "Psalm 23:6"]).update(
                strength=accounts.memorymodel.LEARNED + 0.01
            )

            cvss_review, cvss_learn = i.passages_for_reviewing_and_learning()
            assert cvss_learn == []
            cvs = cvss_review[0]

            assert cvs.group_testing
            # Fully learned verses should not be counted in this total
            assert cvs.needs_testing_count == 2
            assert cvs.total_verse_count == 6

            # We should skip the fully learned first section, and choose the second.
            assert cvs.next_section_verse_count == 3

            passage_uvss = i.verse_statuses_for_passage(cvs.verse_set.id, cvs.version.id)
            section_uvss = i.get_next_section(passage_uvss, cvs.verse_set, add_buffer=False)
            assert [uvs.localized_reference for uvs in section_uvss] == ["Psalm 23:3", "Psalm 23:4", "Psalm 23:5"]

            # Now we actually test the verses in that section that we need to
            for uvs in section_uvss:
                if uvs.localized_reference in ["Psalm 23:3"]:
                    assert uvs.needs_testing
                    i.record_verse_action(uvs.localized_reference, "NET", StageType.TEST, 1.0)
                else:
                    assert not uvs.needs_testing

            # Check again.
            cvss_review, cvss_learn = i.passages_for_reviewing_and_learning()
            cvs = cvss_review[0]
            assert cvs.group_testing
            # We still have 2 that need testing, due to group testing mode.
            assert cvs.needs_testing_count == 2
            assert cvs.total_verse_count == 6
            # But now the next section is the last section, verse 6
            assert cvs.next_section_verse_count == 1

    def test_passages_for_reviewing_and_learning_multiple_versions(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")
        vss1 = i.add_verse_set(vs1, version=self.NET)
        vss2 = i.add_verse_set(vs1, version=self.TCL02)

        assert len(vss1) == 6
        assert len(vss2) == 6

        cvss_learn = i.passages_for_learning()
        assert len(cvss_learn) == 2

        for vn in range(1, 7):
            # NET only:
            ref = "Psalm 23:%d" % vn
            i.record_verse_action(ref, "NET", StageType.TEST, 1.0)
            # Put each one back by n days i.e. as if running over
            # multiple days
            i.verse_statuses.filter(localized_reference=ref).update(
                last_tested=F("last_tested") - timedelta(7 - vn), next_test_due=F("next_test_due") - timedelta(7 - vn)
            )

        cvss_review, cvss_learn = i.passages_for_reviewing_and_learning()
        assert len(cvss_review) == 1
        assert len(cvss_learn) == 1

    def test_issue_138(self):
        # https://github.com/learnscripture/learnscripture.net/issues/138
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")
        i.add_verse_set(vs1)

        for vn in range(1, 7):
            ref = "Psalm 23:%d" % vn
            i.record_verse_action(ref, "NET", StageType.TEST, 1.0)
            # Put all into 'group testing' regime
            i.verse_statuses.filter(localized_reference=ref).update(
                strength=accounts.memorymodel.STRENGTH_FOR_GROUP_TESTING + 0.01
            )
            # Make one due for testing
            if vn == 6:
                now = timezone.now()
                i.verse_statuses.filter(localized_reference=ref).update(
                    last_tested=now - timedelta(10),
                    next_test_due=now - timedelta(1),
                )

        cvss_review, cvss_learn = i.passages_for_reviewing_and_learning()
        # Sanity:
        assert cvss_learn == []
        assert len(cvss_review) == 1
        cvs = cvss_review[0]
        assert cvs.verse_set == vs1
        assert cvs.group_testing
        assert cvs.total_verse_count == 6
        assert cvs.needs_testing_count == 6

    def test_catechisms_for_learning(self):
        i = self.create_identity(version_slug="NET")
        c = TextVersion.objects.get(slug="WSC")
        i.add_catechism(c)
        cs = i.catechisms_for_learning()
        assert len(cs) == 1
        assert cs[0].untested_total == c.qapairs.count()
        assert cs[0].tested_total == 0

        # After one tested:
        i.record_verse_action("Q1", "WSC", StageType.TEST, 1.0)
        cs = i.catechisms_for_learning()
        assert len(cs) == 1
        assert cs[0].untested_total == c.qapairs.count() - 1
        assert cs[0].tested_total == 1

        # After all tested:
        for qapair in c.qapairs.all():
            i.record_verse_action(qapair.localized_reference, "WSC", StageType.TEST, 1.0)
        cs = i.catechisms_for_learning()
        assert len(cs) == 0

    def test_catechisms_for_reviewing(self):
        i = self.create_identity(version_slug="NET")
        c = TextVersion.objects.get(slug="WSC")
        i.add_catechism(c)
        cs = i.catechisms_for_reviewing()
        assert len(cs) == 0

        # After one tested:
        i.record_verse_action("Q1", "WSC", StageType.TEST, 1.0)

        cs = i.catechisms_for_reviewing()
        assert len(cs) == 0

        # Artifically age
        i.verse_statuses.filter(localized_reference="Q1").update(
            last_tested=F("last_tested") - timedelta(days=7), next_test_due=F("next_test_due") - timedelta(days=6)
        )

        cs = i.catechisms_for_reviewing()
        assert len(cs) == 1
        assert cs[0].needs_reviewing_total == 1

        # After all tested:
        for qapair in c.qapairs.all():
            i.record_verse_action(qapair.localized_reference, "WSC", StageType.TEST, 1.0)
        cs = i.catechisms_for_reviewing()
        assert len(cs) == 0

    def test_verse_statuses_for_passage(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")
        i.add_verse_set(vs1)

        uvss = i.verse_statuses_for_passage(vs1.id, self.NET.id)

        assert [uvs.localized_reference for uvs in uvss] == [
            "Psalm 23:1",
            "Psalm 23:2",
            "Psalm 23:3",
            "Psalm 23:4",
            "Psalm 23:5",
            "Psalm 23:6",
        ]

        # Now test and age them:
        for uvs in uvss:
            i.record_verse_action(uvs.localized_reference, "NET", StageType.TEST, 1.0)

        now = timezone.now()
        i.verse_statuses.filter(localized_reference__startswith="Psalm 23").update(
            strength=0.7, last_tested=now, next_test_due=now + timedelta(10)
        )

        # Move one of them back to needing testing
        i.verse_statuses.filter(localized_reference="Psalm 23:3").update(
            last_tested=now - timedelta(1000), next_test_due=now - timedelta(500)
        )

        uvss = i.verse_statuses_for_passage(vs1.id, self.NET.id)
        for uvs in uvss:
            assert uvs.needs_testing_individual == (uvs.localized_reference == "Psalm 23:3")
            assert uvs.needs_testing

    def test_get_next_section(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")
        vs1.breaks = "BOOK18 23:3,BOOK18 23:5"  # break at v3 and v5 - unrealistic!
        vs1.save()
        i.add_verse_set(vs1)

        for vn in range(1, 7):
            ref = "Psalm 23:%d" % vn
            i.record_verse_action(ref, "NET", StageType.TEST, 1.0)
            i.verse_statuses.filter(localized_reference=ref).update(
                last_tested=F("last_tested") - timedelta(10),
                next_test_due=F("next_test_due") - timedelta(10),
            )

        # Shouldn't be splittable yet, since strength will be below threshold
        vss = i.passages_for_reviewing_and_learning()[0]
        assert len(vss) == 1
        assert vss[0].verse_set.name == "Psalm 23"
        assert not vss[0].splittable
        assert vss[0].needs_testing_count == 6
        assert vss[0].total_verse_count == 6

        for vn in range(1, 7):
            ref = "Psalm 23:%d" % vn
            # Now, move each to beyond the threshold which triggers
            # group testing.
            # Put each 1 minute apart, to simulate having tested the whole
            # group together.
            for uvs in i.verse_statuses.filter(localized_reference=ref):
                uvs.last_tested = timezone.now() - timedelta(200 - (vn * 60.0) / (3600.0 * 24))
                uvs.strength = accounts.memorymodel.STRENGTH_FOR_GROUP_TESTING + 0.01
                uvs.next_test_due = uvs.last_tested + timedelta(
                    seconds=accounts.memorymodel.next_test_due_after(uvs.strength)
                )
                uvs.save()

        vss = i.passages_for_reviewing_and_learning()[0]
        assert len(vss) == 1
        assert vss[0].verse_set.name == "Psalm 23"
        assert vss[0].splittable
        assert vss[0].needs_testing_count == 6
        assert vss[0].next_section_verse_count == 2

        # Now test verse_statuses_for_passage/get_next_section in this context:
        uvss1 = i.verse_statuses_for_passage(vs1.id, self.NET.id)
        uvss1 = i.get_next_section(uvss1, vs1)

        # uvss should be first two verses only:
        assert ["Psalm 23:1", "Psalm 23:2"] == [uvs.localized_reference for uvs in uvss1]

        # Now if we learn these two...
        for uvs in uvss1:
            i.record_verse_action(uvs.localized_reference, "NET", StageType.TEST, 0.95)

        # ...then we should get the next two. But we also get a verse
        # of context.

        uvss2 = i.verse_statuses_for_passage(vs1.id, self.NET.id)
        uvss2 = i.get_next_section(uvss2, vs1)

        assert ["Psalm 23:2", "Psalm 23:3", "Psalm 23:4"] == [uvs.localized_reference for uvs in uvss2]
        assert [False, True, True] == [uvs.needs_testing for uvs in uvss2]

        # A quick gap
        with travel(timezone.now() + timedelta(seconds=10)) as tm:

            # Learn next two.

            for uvs in uvss2:
                i.record_verse_action(uvs.localized_reference, "NET", StageType.TEST, 0.95)

            uvss3 = i.verse_statuses_for_passage(vs1.id, self.NET.id)
            uvss3 = i.get_next_section(uvss3, vs1)

            assert ["Psalm 23:4", "Psalm 23:5", "Psalm 23:6"] == [uvs.localized_reference for uvs in uvss3]
            assert [False, True, True] == [uvs.needs_testing for uvs in uvss3]

            # Learn next two.
            tm.shift(timedelta(seconds=10))
            for uvs in uvss3:
                i.record_verse_action(uvs.localized_reference, "NET", StageType.TEST, 0.95)

            # Should wrap around now:
            uvss4 = i.verse_statuses_for_passage(vs1.id, self.NET.id)
            uvss4 = i.get_next_section(uvss4, vs1)

            assert ["Psalm 23:1", "Psalm 23:2"] == [uvs.localized_reference for uvs in uvss4]

    def test_slim_passage_for_reviewing(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")
        vs1.breaks = "BOOK18 23:3,BOOK18 23:5"  # break at v3 and v5
        vs1.save()
        i.add_verse_set(vs1)

        for vn in range(1, 7):
            ref = "Psalm 23:%d" % vn
            i.record_verse_action(ref, "NET", StageType.TEST, 1.0)

            # Make one of them needing testing
        i.verse_statuses.filter(localized_reference="Psalm 23:5").update(next_test_due=timezone.now() - timedelta(1))

        uvss = i.verse_statuses_for_passage(vs1.id, self.NET.id)
        assert len(uvss) == 6

        uvss = i.slim_passage_for_reviewing(uvss, vs1)
        assert [uvs.localized_reference for uvs in uvss] == ["Psalm 23:4", "Psalm 23:5", "Psalm 23:6"]

    def test_get_verse_statuses(self):
        i = self.create_identity()
        vs1 = VerseSet.objects.get(name="Psalm 23")
        uvss = list(i.add_verse_set(vs1))

        # Create some WordSuggestionData
        for uvs in uvss:
            WordSuggestionData.objects.get_or_create(
                version_slug=uvs.version.slug, localized_reference=uvs.localized_reference, defaults={"suggestions": []}
            )
        with self.assertNumQueries(2, using="default"):
            with self.assertNumQueries(1, using="wordsuggestions"):
                d = i.get_verse_statuses_bulk([uvs.id for uvs in uvss])
                assert d[uvss[1].id].localized_reference == uvss[1].localized_reference
                [uvs.scoring_text_words for uvs in d.values()]

    def test_add_verse_choice(self):
        i = self.create_identity()
        uvs1 = i.add_verse_choice("Psalm 23:1")
        assert uvs1.localized_reference == "Psalm 23:1"
        assert [uvs.localized_reference for uvs in i.verse_statuses.all()] == ["Psalm 23:1"]
        # Second add:
        uvs2 = i.add_verse_choice("Psalm 23:1")
        assert uvs1 == uvs2

    def test_add_verse_choice_combo(self):
        i = self.create_identity()
        uvs1 = i.add_verse_choice("Psalm 23:1-2")
        assert uvs1.localized_reference == "Psalm 23:1-2"
        assert [uvs.localized_reference for uvs in i.verse_statuses.all()] == ["Psalm 23:1-2"]
        # Second add:
        uvs2 = i.add_verse_choice("Psalm 23:1-2")
        assert uvs1 == uvs2

    def test_add_verse_choice_merged(self):
        i = self.create_identity(version_slug="TCL02")
        uvs1 = i.add_verse_choice("Romalılar 3:25")
        assert uvs1.localized_reference == "Romalılar 3:25-26"
        assert [uvs.localized_reference for uvs in i.verse_statuses.all()] == ["Romalılar 3:25-26"]
        # Second add:
        uvs2 = i.add_verse_choice("Romalılar 3:25")
        assert uvs1 == uvs2

    def test_add_verse_choice_merged_and_combo(self):
        i = self.create_identity(version_slug="TCL02")
        uvs1 = i.add_verse_choice("Romalılar 3:24-25")
        assert uvs1.localized_reference == "Romalılar 3:24-26"
        assert [uvs.localized_reference for uvs in i.verse_statuses.all()] == ["Romalılar 3:24-26"]
        # Second add:
        uvs2 = i.add_verse_choice("Romalılar 3:24-25")
        assert uvs1 == uvs2

    def test_add_verse_choice_copies_strength(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")
        i.add_verse_set(vs1)

        i.record_verse_action("Psalm 23:1", "NET", StageType.TEST, 1)
        assert i.verse_statuses.get(localized_reference="Psalm 23:1").strength != 0

        # Now use add_verse_choice
        i.add_verse_choice("Psalm 23:1")

        # We need two UserVerseStatuses, because the user wants to learn this
        # verse outside the context of the passage.
        assert i.verse_statuses.filter(localized_reference="Psalm 23:1").count() == 2

        assert not (0.0 in [uvs.strength for uvs in i.verse_statuses.filter(localized_reference="Psalm 23:1")])

    def test_verses_started_milestone_event(self):
        # This reproduces a bit of the logic from ActionCompleteHandler in order
        # to test Identity.award_action_points

        i, account = self.create_account(version_slug="KJV")

        refs = ["Genesis 1:%d" % j for j in range(1, 11)] + ["Genesis 2:%d" % j for j in range(1, 3)]

        for j, ref in enumerate(refs):
            i.add_verse_choice(ref)
            action_change = i.record_verse_action(ref, "KJV", StageType.TEST, 1)
            i.award_action_points(
                ref,
                LANG.EN,
                Verse.objects.get(localized_reference=ref, version__slug="KJV").text,
                MemoryStage.SEEN,
                action_change,
                StageType.TEST,
                1,
            )

            assert Event.objects.filter(event_type=EventType.VERSES_STARTED_MILESTONE).count() == (0 if j < 9 else 1)

    def test_verses_finished_milestone_event(self):
        i, account = self.create_account(version_slug="KJV")

        refs = ["Genesis 1:%d" % j for j in range(1, 11)] + ["Genesis 2:%d" % j for j in range(1, 3)]

        for j, ref in enumerate(refs):
            i.add_verse_choice(ref)
            i.record_verse_action(ref, "KJV", StageType.TEST, 1)
            # Move to nearly learned:
            i.verse_statuses.filter(localized_reference=ref).update(
                strength=accounts.memorymodel.LEARNED - 0.001, last_tested=timezone.now() - timedelta(100)
            )
            # Final test, moving to above LEARNED
            action_change = i.record_verse_action(ref, "KJV", StageType.TEST, 1)
            i.award_action_points(
                ref,
                LANG.EN,
                Verse.objects.get(localized_reference=ref, version__slug="KJV").text,
                MemoryStage.TESTED,
                action_change,
                StageType.TEST,
                1,
            )
            assert Event.objects.filter(event_type=EventType.VERSES_FINISHED_MILESTONE).count() == (0 if j < 9 else 1)

    def test_order_after_cancelling_and_re_adding_verse(self):
        """
        If a verse is added, then cancelled, then added again as part of a set,
        the order of learning should be the order defined in the set.
        """
        i = self.create_identity(version_slug="NET")
        i.add_verse_choice("John 14:6")
        assert [uvs.localized_reference for uvs in i.bible_verse_statuses_for_learning(None)] == ["John 14:6"]
        i.record_verse_action("John 14:6", "NET", StageType.READ, 1)
        i.cancel_learning(["John 14:6"], "NET")

        vs1 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs1)

        assert [uvs.localized_reference for uvs in i.bible_verse_statuses_for_learning(vs1.id)] == [
            "John 3:16",
            "John 14:6",
            "Ephesians 2:8-9",
        ]

    def test_issue_75(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")

        # Change it so that it misses the last verse
        vs1.set_verse_choices(["BOOK18 23:1", "BOOK18 23:2", "BOOK18 23:3", "BOOK18 23:4", "BOOK18 23:5"])

        # Now add it
        i.add_verse_set(vs1)

        uvss = i.verse_statuses_for_passage(vs1.id, self.NET.id)
        assert [uvs.localized_reference for uvs in uvss] == [
            "Psalm 23:1",
            "Psalm 23:2",
            "Psalm 23:3",
            "Psalm 23:4",
            "Psalm 23:5",
        ]

        # Now learn a standalone verse choice
        i.add_verse_choice("Psalm 23:6")

        # Add the verse back to the set
        VerseChoice.objects.create(internal_reference="BOOK18 23:6", verse_set=vs1, set_order=6)

        # Now 'press' the learn button again
        i.add_verse_set(vs1)

        # Should have all verses this time
        uvss = i.verse_statuses_for_passage(vs1.id, self.NET.id)
        assert [uvs.localized_reference for uvs in uvss] == [
            "Psalm 23:1",
            "Psalm 23:2",
            "Psalm 23:3",
            "Psalm 23:4",
            "Psalm 23:5",
            "Psalm 23:6",
        ]

    def test_add_missing_verse(self):
        """
        Should be able to create a UVS against a missing verse.
        """
        i = self.create_identity()
        version = i.default_bible_version
        version.verse_set.get(localized_reference="John 3:16").mark_missing()
        with override("en"):
            i.add_verse_choice("John 3:16")
        assert i.verse_statuses.filter(localized_reference="John 3:16", version=version).count() == 0

    def test_consistent_learner_award(self):
        import awards.tasks

        identity, account = self.create_account(version_slug="KJV")

        def learn(i):
            # We simulate testing over time by moving previous data back a day
            identity.verse_statuses.update(first_seen=F("first_seen") - timedelta(days=1))
            ref = "Genesis 1:%d" % i
            identity.add_verse_choice(ref)
            identity.record_verse_action(ref, "KJV", StageType.TEST, 1.0)

        for i in range(1, 10):
            learn(i)
            # Simulate the cronjob that runs
            awards.tasks.give_all_consistent_learner_awards()

            assert account.awards.filter(award_type=AwardType.CONSISTENT_LEARNER).count() == (0 if i < 7 else 1)

    def test_verse_sets_chosen(self):
        i = self.create_identity(version_slug="NET")

        with self.assertNumQueries(1):
            assert i.verse_sets_chosen() == []

        vs1 = VerseSet.objects.get(name="Psalm 23")
        i.add_verse_set(vs1)
        with self.assertNumQueries(3):
            chosen_1 = i.verse_sets_chosen()
        assert chosen_1 == [ChosenVerseSet(verse_set=vs1, version=i.default_bible_version)]

        i.add_verse_set(vs1, version=self.KJV)

        with self.assertNumQueries(3):
            chosen_2 = i.verse_sets_chosen()
        assert chosen_2 == [
            ChosenVerseSet(verse_set=vs1, version=self.KJV),
            ChosenVerseSet(verse_set=vs1, version=i.default_bible_version),
        ]

        vs2 = VerseSet.objects.get(name="Bible 101")
        i.add_verse_set(vs2)

        with self.assertNumQueries(3):
            chosen_3 = i.verse_sets_chosen()
        assert chosen_3 == [
            ChosenVerseSet(verse_set=vs2, version=i.default_bible_version),
            ChosenVerseSet(verse_set=vs1, version=self.KJV),
            ChosenVerseSet(verse_set=vs1, version=i.default_bible_version),
        ]

    def test_next_verse_due(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Bible 101")

        # Initial
        assert i.next_verse_due() is None

        # Added a verse
        i.add_verse_set(vs1)
        assert i.next_verse_due() is None

        i.record_verse_action("John 3:16", "NET", StageType.TEST, 1)
        nv = i.next_verse_due()
        assert nv.localized_reference == "John 3:16"

    def test_next_verse_due_ignores_passages_in_initial_learning(self):
        i = self.create_identity(version_slug="NET")
        vs1 = VerseSet.objects.get(name="Psalm 23")

        # Added a verse
        i.add_verse_set(vs1)
        assert i.next_verse_due() is None

        i.record_verse_action("Psalm 23:1", "NET", StageType.TEST, 1)
        assert i.next_verse_due() is None
