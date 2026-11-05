from __future__ import annotations

import unittest

from tools.rtd.site_role import PRIVATE_RTD_PROJECTS, resolve_site_role

PRIVATE = "ht-docs-ht-manuals"
PUBLIC = "ht-docs-ht-user-manuals"


def rtd(project: str) -> dict[str, str]:
    """The variables Read the Docs exports to a project's builds."""
    return {"READTHEDOCS": "True", "READTHEDOCS_PROJECT": project}


class SiteRoleTests(unittest.TestCase):
    def role(self, requested, environ):
        return resolve_site_role(requested, environ)[0]

    def test_the_private_project_is_listed_and_the_public_one_is_not(self):
        self.assertIn(PRIVATE, PRIVATE_RTD_PROJECTS)
        self.assertNotIn(PUBLIC, PRIVATE_RTD_PROJECTS)

    def test_local_builds_keep_the_combined_default(self):
        self.assertEqual(self.role("", {}), "combined")
        self.assertEqual(self.role(None, {}), "combined")
        self.assertEqual(self.role("manuals", {}), "manuals")
        self.assertEqual(self.role("combined", {}), "combined")

    def test_the_listed_private_project_builds_combined_unless_told_otherwise(self):
        self.assertEqual(self.role("", rtd(PRIVATE)), "combined")
        self.assertEqual(self.role("combined", rtd(PRIVATE)), "combined")
        self.assertEqual(self.role("manuals", rtd(PRIVATE)), "manuals")

    def test_any_other_project_builds_manuals_even_without_the_variable(self):
        # 2026-11-04: the public project had no RTD_SITE_ROLE and served the knowledge base.
        for project in (PUBLIC, "ht-docs-new-project", ""):
            with self.subTest(project):
                self.assertEqual(self.role("", rtd(project)), "manuals")
                self.assertEqual(self.role("manuals", rtd(project)), "manuals")
        self.assertEqual(self.role("", {"READTHEDOCS_PROJECT": PUBLIC}), "manuals")

    def test_combined_on_an_unlisted_project_fails_the_build(self):
        with self.assertRaisesRegex(ValueError, "PRIVATE_RTD_PROJECTS"):
            resolve_site_role("combined", rtd(PUBLIC))

    def test_unknown_roles_fail_and_typed_values_are_normalised(self):
        for environ in ({}, rtd(PRIVATE), rtd(PUBLIC)):
            with self.subTest(environ), self.assertRaisesRegex(ValueError, "rtd_site_role"):
                resolve_site_role("public", environ)
        self.assertEqual(self.role(" Manuals ", rtd(PRIVATE)), "manuals")

    def test_the_reason_names_the_project(self):
        self.assertIn(PUBLIC, resolve_site_role("", rtd(PUBLIC))[1])
        self.assertEqual(resolve_site_role("", {})[1], "local build")


if __name__ == "__main__":
    unittest.main()
