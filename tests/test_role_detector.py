import unittest

from role_detector import detect_role


class RoleDetectorTests(unittest.TestCase):
    def test_detects_support_role(self) -> None:
        job_description = (
            "Technical Support Engineer, SQL, troubleshooting, customer support"
        )

        self.assertEqual(detect_role(job_description), "support")

    def test_detects_developer_role(self) -> None:
        job_description = (
            "Junior Python Developer, APIs, backend, Git, web applications"
        )

        self.assertEqual(detect_role(job_description), "developer")

    def test_detects_cybersecurity_role(self) -> None:
        job_description = (
            "Junior SOC Analyst, SIEM, incident response, vulnerability, "
            "security events"
        )

        self.assertEqual(detect_role(job_description), "cybersecurity")


if __name__ == "__main__":
    unittest.main()
