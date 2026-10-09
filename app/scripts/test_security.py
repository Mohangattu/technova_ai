import sys
from pathlib import Path

_APP_DIR = Path(__file__).parent.parent
_INGESTION_DIR = _APP_DIR / "ingestion"
_RETRIEVAL_DIR = _APP_DIR / "retrieval"

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_INGESTION_DIR))
sys.path.insert(0, str(_RETRIEVAL_DIR))


from retrieval.access_control import AccessController


# --------------------------------
# Security Test
# --------------------------------

access_controller = AccessController()


def test_access_matrix():

    expected = {
        "EMPLOYEE": {
            "EMPLOYEE": True,
            "MANAGER": False,
            "AI_ENGINEER":False,
            "ADMIN": False,
        },
        "MANAGER": {
            "EMPLOYEE": True,
            "MANAGER": True,
            "AI_ENGINEER":False,
            "ADMIN": False,
        },
        "AI_ENGINEER":{
            "EMPLOYEE": True,
            "MANAGER": True,
            "AI_ENGINEER":True,
            "ADMIN": False,
        },
        "ADMIN": {
            "EMPLOYEE": True,
            "MANAGER": True,
            "AI_ENGINEER":True,
            "ADMIN": True,
        },
    }

    print("\nACCESS CONTROL MATRIX")

    all_passed = True

    for user_level, documents in expected.items():

        for document_level, expected_result in documents.items():

            actual_result = (
                access_controller.can_access(
                    user_level,
                    document_level,
                )
            )

            passed = (
                actual_result == expected_result
            )

            status = "PASS" if passed else "FAIL"

            print(
                f"{status} | "
                f"User={user_level:<8} "
                f"Document={document_level:<8} "
                f"Allowed={actual_result}"
            )

            if not passed:
                all_passed = False

    return all_passed


# --------------------------------
# Invalid Access Level Tests
# --------------------------------

def test_invalid_access_levels():

    print("\nINVALID ACCESS LEVEL TESTS")

    all_passed = True

    try:

        access_controller.validate_access_level(
            "GUEST"
        )

        print(
            "FAIL | GUEST was accepted"
        )

        all_passed = False

    except ValueError:

        print(
            "PASS | GUEST was rejected"
        )

    try:

        access_controller.validate_access_level(
            "SUPERADMIN"
        )

        print(
            "FAIL | SUPERADMIN was accepted"
        )

        all_passed = False

    except ValueError:

        print(
            "PASS | SUPERADMIN was rejected"
        )

    return all_passed


# --------------------------------
# Run Tests
# --------------------------------

matrix_passed = test_access_matrix()

invalid_passed = test_invalid_access_levels()


print("\n" + "=" * 50)

if matrix_passed and invalid_passed:

    print("ALL SECURITY TESTS PASSED")

else:

    print("SECURITY TESTS FAILED")

print("=" * 50)