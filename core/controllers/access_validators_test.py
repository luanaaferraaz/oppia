# Copyright 2021 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for core.domain.access_validator."""

from __future__ import annotations

import datetime

from core import feature_flag_list
from core import feconf
from core.domain import classroom_config_domain
from core.domain import classroom_config_services
from core.domain import learner_group_fetchers
from core.domain import learner_group_services
from core.domain import rights_manager
from core.domain import user_services
from core.platform import models
from core.storage.blog import gae_models as blog_models
from core.tests import test_utils

from typing import Final

MYPY = False
if MYPY:  # pragma: no cover
    from mypy_imports import blog_models

(blog_models,) = models.Registry.import_models([models.Names.BLOG])

ACCESS_VALIDATION_HANDLER_PREFIX: Final = (
    feconf.ACCESS_VALIDATION_HANDLER_PREFIX
)


class ClassroomPageAccessValidationHandlerTests(test_utils.GenericTestBase):

    def setUp(self) -> None:
        super().setUp()
        self.signup(
            self.CURRICULUM_ADMIN_EMAIL, self.CURRICULUM_ADMIN_USERNAME)
        self.set_curriculum_admins([self.CURRICULUM_ADMIN_USERNAME])
        self.user_id_admin = (
            self.get_user_id_from_email(self.CURRICULUM_ADMIN_EMAIL))
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)
        math_classroom_dict: classroom_config_domain.ClassroomDict = {
            'classroom_id': 'math_classroom_id',
            'name': 'math',
            'url_fragment': 'math',
            'course_details': 'Course details for classroom.',
            'topic_list_intro': 'Topics covered for classroom',
            'topic_id_to_prerequisite_topic_ids': {}
        }
        math_classroom = classroom_config_domain.Classroom.from_dict(
            math_classroom_dict)

        classroom_config_services.create_new_classroom(math_classroom)

    def test_validation_returns_true_if_classroom_is_available(self) -> None:
        self.login(self.EDITOR_EMAIL)
        self.get_html_response(
            '%s/can_access_classroom_page?classroom_url_fragment=%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, 'math'))

    def test_validation_returns_false_if_classroom_doesnot_exists(self) -> None:
        self.login(self.EDITOR_EMAIL)
        self.get_json(
            '%s/can_access_classroom_page?classroom_url_fragment=%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, 'not_valid'),
            expected_status_int=404)


class CollectionViewerPageAccessValidationHandlerTests(
        test_utils.GenericTestBase):
    """Test for collection page access validation."""

    COLLECTION_ID: Final = 'cid'
    OTHER_EDITOR_EMAIL: Final = 'another@example.com'

    def setUp(self) -> None:
        """Before each individual test, create a dummy collection."""
        super().setUp()
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)
        self.editor = user_services.get_user_actions_info(self.editor_id)
        self.signup(self.NEW_USER_EMAIL, self.NEW_USER_USERNAME)
        self.new_user_id = self.get_user_id_from_email(self.NEW_USER_EMAIL)
        self.save_new_valid_collection(self.COLLECTION_ID, self.editor_id)

    def test_unpublished_collections_are_invisible_to_logged_out_users(
        self
    ) -> None:
        self.get_json(
            '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID),
            expected_status_int=404)

    def test_unpublished_collections_are_invisible_to_unconnected_users(
        self
    ) -> None:
        self.login(self.NEW_USER_EMAIL)
        self.get_json(
        '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID),
        expected_status_int=404)
        self.logout()

    def test_unpublished_collections_are_invisible_to_other_editors(
        self
    ) -> None:
        self.signup(self.OTHER_EDITOR_EMAIL, 'othereditorusername')
        self.save_new_valid_collection('cid2', self.OTHER_EDITOR_EMAIL)
        self.login(self.OTHER_EDITOR_EMAIL)
        self.get_json(
        '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID),
        expected_status_int=404)
        self.logout()

    def test_unpublished_collections_are_visible_to_their_editors(
        self
    ) -> None:
        self.login(self.EDITOR_EMAIL)
        self.get_html_response(
            '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID))
        self.logout()

    def test_unpublished_collections_are_visible_to_admins(self) -> None:
        self.signup(self.MODERATOR_EMAIL, self.MODERATOR_USERNAME)
        self.set_moderators([self.MODERATOR_USERNAME])
        self.login(self.MODERATOR_EMAIL)
        self.get_html_response(
            '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID))
        self.logout()

    def test_published_collections_are_visible_to_logged_out_users(
        self
    ) -> None:
        rights_manager.publish_collection(self.editor, self.COLLECTION_ID)

        self.get_html_response(
            '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID))

    def test_published_collections_are_visible_to_logged_in_users(
        self
    ) -> None:
        rights_manager.publish_collection(self.editor, self.COLLECTION_ID)
        self.login(self.NEW_USER_EMAIL)
        self.get_html_response(
            '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID))

    def test_invalid_collection_error(self) -> None:
        self.login(self.EDITOR_EMAIL)
        self.get_json(
            '%s/can_access_collection_player_page/%s' %
            (ACCESS_VALIDATION_HANDLER_PREFIX, 'none'),
            expected_status_int=404)
        self.logout()


class ReleaseCoordinatorAccessValidationHandlerTests(
        test_utils.GenericTestBase):
    """Test for release coordinator access validation."""

    def setUp(self) -> None:
        """Complete the signup process for self.RELEASE_COORDINATOR_EMAIL."""
        super().setUp()
        self.signup(
            self.RELEASE_COORDINATOR_EMAIL, self.RELEASE_COORDINATOR_USERNAME)
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)

        self.add_user_role(
            self.RELEASE_COORDINATOR_USERNAME,
            feconf.ROLE_ID_RELEASE_COORDINATOR)

    def test_guest_user_does_not_pass_validation(self) -> None:
        self.get_json(
            '%s/can_access_release_coordinator_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=401)

    def test_exploration_editor_does_not_pass_validation(self) -> None:
        self.login(self.EDITOR_EMAIL)
        self.get_json(
            '%s/can_access_release_coordinator_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=401)

    def test_release_coordinator_passes_validation(self) -> None:
        self.login(self.RELEASE_COORDINATOR_EMAIL)

        self.get_html_response(
            '%s/can_access_release_coordinator_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX)


class DiagnosticTestPlayerPageAccessValidationHandlerTests(
        test_utils.GenericTestBase):
    """Test for diagnostic test player access validation."""

    def test_should_not_access_diagnostic_test_page_when_feature_is_disabled(
        self) -> None:
        self.get_json(
            '%s/can_access_diagnostic_test_player_page' % (
                ACCESS_VALIDATION_HANDLER_PREFIX),
                expected_status_int=404)

    @test_utils.enable_feature_flags(
        [feature_flag_list.FeatureNames.DIAGNOSTIC_TEST])
    def test_should_access_diagnostic_test_page_when_feature_is_enabled(
        self) -> None:
        self.get_html_response(
           '%s/can_access_diagnostic_test_player_page' % (
                ACCESS_VALIDATION_HANDLER_PREFIX),
            expected_status_int=200
        )


class ProfileExistsValidationHandlerTests(test_utils.GenericTestBase):

    def setUp(self) -> None:
        super().setUp()
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.signup(self.VIEWER_EMAIL, self.VIEWER_USERNAME)

    def test_profile_validation_returns_true_if_user_views_other_profile(
        self
    ) -> None:
        # Viewer looks at editor's profile page.
        self.login(self.VIEWER_EMAIL)
        self.get_html_response(
            '%s/does_profile_exist/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.EDITOR_USERNAME))
        self.logout()

    def test_profile_validation_returns_true_if_user_views_own_profile(
        self
    ) -> None:
        # Editor looks at their own profile page.
        self.login(self.EDITOR_EMAIL)
        self.get_html_response(
            '%s/does_profile_exist/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.EDITOR_USERNAME))
        self.logout()

    def test_profile_validation_returns_false_if_profile_doesnot_exist(
        self
    ) -> None:
        # Editor looks at non-existing profile page.
        self.login(self.EDITOR_EMAIL)
        self.get_json(
            '%s/does_profile_exist/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.BLOG_ADMIN_USERNAME),
                expected_status_int=404)
        self.logout()


class ManageOwnAccountValidationHandlerTests(test_utils.GenericTestBase):

    banned_user = 'banneduser'
    banned_user_email = 'banned@example.com'
    username = 'user'
    user_email = 'user@example.com'

    def setUp(self) -> None:
        super().setUp()
        self.signup(self.banned_user_email, self.banned_user)
        self.signup(self.user_email, self.username)
        self.mark_user_banned(self.banned_user)

    def test_banned_user_cannot_manage_account(self) -> None:
        self.login(self.banned_user_email)
        self.get_json(
            '%s/can_manage_own_account' % ACCESS_VALIDATION_HANDLER_PREFIX,
            expected_status_int=401)

    def test_normal_user_can_manage_account(self) -> None:
        self.login(self.user_email)
        self.get_html_response(
            '%s/can_manage_own_account' % ACCESS_VALIDATION_HANDLER_PREFIX)
        self.logout()


class ViewLearnerGroupPageAccessValidationHandlerTests(
    test_utils.GenericTestBase
):

    def setUp(self) -> None:
        super().setUp()
        self.signup(self.NEW_USER_EMAIL, self.NEW_USER_USERNAME)
        self.signup(
            self.CURRICULUM_ADMIN_EMAIL, self.CURRICULUM_ADMIN_USERNAME)

        self.facilitator_id = self.get_user_id_from_email(
            self.CURRICULUM_ADMIN_EMAIL)
        self.learner_id = self.get_user_id_from_email(self.NEW_USER_EMAIL)

        self.LEARNER_GROUP_ID = (
            learner_group_fetchers.get_new_learner_group_id()
        )
        learner_group_services.create_learner_group(
            self.LEARNER_GROUP_ID, 'Learner Group Title', 'Description',
            [self.facilitator_id], [self.learner_id],
            ['subtopic_id_1'], ['story_id_1'])

        self.login(self.NEW_USER_EMAIL)

    def test_validation_returns_false_with_learner_groups_feature_disabled(
        self
    ) -> None:
        self.get_json(
            '%s/does_learner_group_exist/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.LEARNER_GROUP_ID),
                expected_status_int=404)
        self.logout()

    @test_utils.enable_feature_flags(
        [feature_flag_list.FeatureNames.LEARNER_GROUPS_ARE_ENABLED])
    def test_validation_returns_false_with_user_not_being_a_learner(
        self
    ) -> None:
        self.get_json(
            '%s/does_learner_group_exist/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.LEARNER_GROUP_ID),
                expected_status_int=404)
        self.logout()

    @test_utils.enable_feature_flags(
        [feature_flag_list.FeatureNames.LEARNER_GROUPS_ARE_ENABLED])
    def test_validation_returns_true_for_valid_learner(self) -> None:
        learner_group_services.add_learner_to_learner_group(
            self.LEARNER_GROUP_ID, self.learner_id, False)
        self.get_html_response(
            '%s/does_learner_group_exist/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.LEARNER_GROUP_ID))


class EditLearnerGroupPageAccessValidationHandlerTests(
    test_utils.GenericTestBase
):

    def setUp(self) -> None:
        super().setUp()
        self.signup(self.NEW_USER_EMAIL, self.NEW_USER_USERNAME)
        self.signup(
            self.CURRICULUM_ADMIN_EMAIL, self.CURRICULUM_ADMIN_USERNAME)

        self.facilitator_id = self.get_user_id_from_email(
            self.CURRICULUM_ADMIN_EMAIL)

        self.LEARNER_GROUP_ID = (
            learner_group_fetchers.get_new_learner_group_id()
        )
        learner_group_services.create_learner_group(
            self.LEARNER_GROUP_ID, 'Learner Group Title', 'Description',
            [self.facilitator_id], [],
            ['subtopic_id_1'], ['story_id_1'])

    def test_validation_returns_false_with_learner_groups_feature_disabled(
        self
    ) -> None:
        self.login(self.CURRICULUM_ADMIN_EMAIL)
        self.get_json(
            '%s/can_access_edit_learner_group_page/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.LEARNER_GROUP_ID),
                expected_status_int=404)

    @test_utils.enable_feature_flags(
        [feature_flag_list.FeatureNames.LEARNER_GROUPS_ARE_ENABLED])
    def test_validation_returns_false_with_user_not_being_a_facilitator(
        self
    ) -> None:
        self.login(self.NEW_USER_EMAIL)
        self.get_json(
            '%s/can_access_edit_learner_group_page/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.LEARNER_GROUP_ID),
                expected_status_int=404)

    @test_utils.enable_feature_flags(
        [feature_flag_list.FeatureNames.LEARNER_GROUPS_ARE_ENABLED])
    def test_validation_returns_true_for_valid_facilitator(self) -> None:
        self.login(self.CURRICULUM_ADMIN_EMAIL)
        self.get_html_response(
            '%s/can_access_edit_learner_group_page/%s' % (
                ACCESS_VALIDATION_HANDLER_PREFIX, self.LEARNER_GROUP_ID))


class FacilitatorDashboardPageAccessValidationHandlerTests(
        test_utils.GenericTestBase):
    """Test for facilitator dashboard access validation."""

    def setUp(self) -> None:
        super().setUp()
        self.signup(self.NEW_USER_EMAIL, self.NEW_USER_USERNAME)

    def test_should_not_access_facilitator_dashboard_when_feature_is_disabled(
        self) -> None:
        self.login(self.NEW_USER_EMAIL)
        self.get_json(
            '%s/can_access_facilitator_dashboard_page' % (
                ACCESS_VALIDATION_HANDLER_PREFIX),
                expected_status_int=404)

    @test_utils.enable_feature_flags(
        [feature_flag_list.FeatureNames.LEARNER_GROUPS_ARE_ENABLED])
    def test_should_access_facilitator_dashboard_page_when_feature_is_enabled(
        self) -> None:
        self.login(self.NEW_USER_EMAIL)
        self.get_html_response(
           '%s/can_access_facilitator_dashboard_page' % (
                ACCESS_VALIDATION_HANDLER_PREFIX),
            expected_status_int=200
        )


class CreateLearnerGroupPageAccessValidationHandlerTests(
    test_utils.GenericTestBase
):

    def setUp(self) -> None:
        super().setUp()
        self.signup(self.NEW_USER_EMAIL, self.NEW_USER_USERNAME)

    def test_validation_returns_false_with_learner_groups_feature_disabled(
        self
    ) -> None:
        self.login(self.NEW_USER_EMAIL)
        self.get_json(
            '%s/can_access_create_learner_group_page' % (
                ACCESS_VALIDATION_HANDLER_PREFIX),
                expected_status_int=404)

    @test_utils.enable_feature_flags(
        [feature_flag_list.FeatureNames.LEARNER_GROUPS_ARE_ENABLED])
    def test_validation_returns_true_for_valid_user(self) -> None:
        self.login(self.NEW_USER_EMAIL)
        self.get_html_response(
            '%s/can_access_create_learner_group_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)


class BlogHomePageAccessValidationHandlerTests(test_utils.GenericTestBase):
    """Checks the access to the blog home page and its rendering."""

    def test_blog_home_page_access_without_logging_in(self) -> None:
        self.get_html_response(
            '%s/can_access_blog_home_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)

    def test_blog_home_page_access_without_having_rights(self) -> None:
        self.signup(self.VIEWER_EMAIL, self.VIEWER_USERNAME)
        self.login(self.VIEWER_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_home_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)
        self.logout()

    def test_blog_home_page_access_as_blog_admin(self) -> None:
        self.signup(self.BLOG_ADMIN_EMAIL, self.BLOG_ADMIN_USERNAME)
        self.add_user_role(
            self.BLOG_ADMIN_USERNAME, feconf.ROLE_ID_BLOG_ADMIN)
        self.login(self.BLOG_ADMIN_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_home_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)
        self.logout()

    def test_blog_home_page_access_as_blog_post_editor(self) -> None:
        self.signup(self.BLOG_EDITOR_EMAIL, self.BLOG_EDITOR_USERNAME)
        self.add_user_role(
            self.BLOG_EDITOR_USERNAME, feconf.ROLE_ID_BLOG_POST_EDITOR)
        self.login(self.BLOG_EDITOR_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_home_page' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)
        self.logout()


class BlogPostPageAccessValidationHandlerTests(test_utils.GenericTestBase):
    """Checks the access to the blog post page and its rendering."""

    def setUp(self) -> None:
        super().setUp()
        blog_post_model = blog_models.BlogPostModel(
            id='blog_one',
            author_id='user_1',
            content='content',
            title='title',
            published_on=datetime.datetime.utcnow(),
            url_fragment='sample-url',
            tags=['news'],
            thumbnail_filename='thumbnail.svg',
        )
        blog_post_model.update_timestamps()
        blog_post_model.put()

    def test_blog_post_page_access_without_logging_in(self) -> None:
        self.get_html_response(
            '%s/can_access_blog_post_page?blog_post_url_fragment=sample-url' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)

    def test_blog_post_page_access_without_having_rights(self) -> None:
        self.signup(self.VIEWER_EMAIL, self.VIEWER_USERNAME)
        self.login(self.VIEWER_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_post_page?blog_post_url_fragment=sample-url' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)
        self.logout()

    def test_blog_post_page_access_as_blog_admin(self) -> None:
        self.signup(self.BLOG_ADMIN_EMAIL, self.BLOG_ADMIN_USERNAME)
        self.add_user_role(
            self.BLOG_ADMIN_USERNAME, feconf.ROLE_ID_BLOG_ADMIN)
        self.login(self.BLOG_ADMIN_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_post_page?blog_post_url_fragment=sample-url' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)
        self.logout()

    def test_blog_post_page_access_as_blog_post_editor(self) -> None:
        self.signup(self.BLOG_EDITOR_EMAIL, self.BLOG_EDITOR_USERNAME)
        self.add_user_role(
            self.BLOG_EDITOR_USERNAME, feconf.ROLE_ID_BLOG_POST_EDITOR)
        self.login(self.BLOG_EDITOR_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_post_page?blog_post_url_fragment=sample-url' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=200)
        self.logout()

    def test_validation_returns_false_if_blog_post_is_not_available(
        self
    ) -> None:
        self.signup(self.BLOG_EDITOR_EMAIL, self.BLOG_EDITOR_USERNAME)
        self.add_user_role(
            self.BLOG_EDITOR_USERNAME, feconf.ROLE_ID_BLOG_POST_EDITOR)
        self.login(self.BLOG_EDITOR_EMAIL)

        self.get_json(
            '%s/can_access_blog_post_page?blog_post_url_fragment=invalid-url' %
            ACCESS_VALIDATION_HANDLER_PREFIX, expected_status_int=404)
        self.logout()


class BlogAuthorProfilePageAccessValidationHandlerTests(
    test_utils.GenericTestBase):
    """Checks the access to the blog author profile page and its rendering."""

    def setUp(self) -> None:
        super().setUp()
        self.signup(self.BLOG_ADMIN_EMAIL, self.BLOG_ADMIN_USERNAME)
        self.add_user_role(
            self.BLOG_ADMIN_USERNAME, feconf.ROLE_ID_BLOG_ADMIN)

    def test_blog_author_profile_page_access_without_logging_in(self) -> None:
        self.get_html_response(
            '%s/can_access_blog_author_profile_page/%s' % (
            ACCESS_VALIDATION_HANDLER_PREFIX, self.BLOG_ADMIN_USERNAME
            ), expected_status_int=200
        )

    def test_blog_author_profile_page_access_after_logging_in(self) -> None:
        self.signup(self.VIEWER_EMAIL, self.VIEWER_USERNAME)
        self.login(self.VIEWER_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_author_profile_page/%s' % (
            ACCESS_VALIDATION_HANDLER_PREFIX, self.BLOG_ADMIN_USERNAME
            ), expected_status_int=200
        )
        self.logout()

    def test_blog_author_profile_page_access_as_blog_admin(self) -> None:
        self.login(self.BLOG_ADMIN_EMAIL)
        self.get_html_response(
            '%s/can_access_blog_author_profile_page/%s' % (
            ACCESS_VALIDATION_HANDLER_PREFIX, self.BLOG_ADMIN_USERNAME
            ), expected_status_int=200
        )
        self.logout()

    def test_validation_returns_false_if_given_user_is_not_blog_post_author(
        self
    ) -> None:
        self.signup(self.VIEWER_EMAIL, self.VIEWER_USERNAME)
        self.login(self.VIEWER_EMAIL)
        self.get_json(
            '%s/can_access_blog_author_profile_page/%s' % (
            ACCESS_VALIDATION_HANDLER_PREFIX, self.VIEWER_USERNAME
            ), expected_status_int=404
        )
        self.logout()

    def test_validation_returns_false_if_given_user_is_non_existent(
        self
    ) -> None:
        self.signup(self.VIEWER_EMAIL, self.VIEWER_USERNAME)
        self.login(self.VIEWER_EMAIL)
        self.get_json(
            '%s/can_access_blog_author_profile_page/invalid_username' % (
            ACCESS_VALIDATION_HANDLER_PREFIX
            ), expected_status_int=404
        )
        self.logout()


class CollectionEditorAccessValidationPage(test_utils.GenericTestBase):
    """Test for collection editor page access validation"""

    COLLECTION_ID: Final = '0'

    def setUp(self) -> None:
        super().setUp()
        self.collection_editor_username = 'collectionEditor'
        self.user_email = 'collectionEditor@example.com'
        self.guest_username = 'guest'
        self.guest_email = 'guest@example.com'

        self.signup(self.user_email, self.collection_editor_username)
        self.signup(self.guest_email, self.guest_username)
        self.add_user_role(
            self.collection_editor_username, feconf.ROLE_ID_COLLECTION_EDITOR)
        self.user_id = self.get_user_id_from_email(self.user_email)
        self.user = user_services.get_user_actions_info(self.user_id)
        self.save_new_valid_collection(self.COLLECTION_ID, self.user_id)

    def test_for_logged_in_user_without_rights(self) -> None:
        self.login(self.guest_email)
        self.get_html_response(
            '%s/can_access_collection_editor_page/%s' % (
            ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID
            ), expected_status_int=401
        )
        self.logout()

    def test_for_logged_in_user_with_rights(self) -> None:
        rights_manager.publish_collection(self.user, self.COLLECTION_ID)
        self.login(self.user_email)
        self.get_html_response(
            '%s/can_access_collection_editor_page/%s' % (
            ACCESS_VALIDATION_HANDLER_PREFIX, self.COLLECTION_ID
            ), expected_status_int=200
        )
        self.logout()

    def test_validation_returns_false_if_given_collection_id_non_existent(
        self) -> None:
        self.login(self.guest_email)
        self.get_html_response(
            '%s/can_access_collection_editor_page/invalid_collectionId' % (
            ACCESS_VALIDATION_HANDLER_PREFIX,
            ), expected_status_int=404
        )
        self.logout()

    def test_should_not_access_for_logged_out_user(self) -> None:
        self.get_html_response(
            '%s/can_access_collection_editor_page/' % (
            ACCESS_VALIDATION_HANDLER_PREFIX,
            ), expected_status_int=404
        )
