from pathlib import Path
import importlib.util
import sys


required_email_functions = [
    "send_email_safely",
    "send_activation_email",
    "build_booking_created_message",
    "send_booking_created_email",
    "build_booking_approved_message",
    "send_booking_approved_email",
    "build_booking_rejected_message",
    "send_booking_rejected_email",
    "build_booking_cancelled_message",
    "send_booking_cancelled_email",
]


# ========================
# Verify Files
# ========================
required_files = [
    Path("app/email.py"),
    Path("app/booking/routes.py"),
    Path("app/admin/routes.py"),
    Path("tests/test_booking_email_messages.py"),
    Path("tests/test_booking_email_integrations.py"),
]

missing_files = [
    str(path)
    for path in required_files
    if not path.exists()
]

if missing_files:
    print(
        "Fail belum lengkap:"
    )

    for path in missing_files:
        print(
            f"- {path}"
        )

    sys.exit(1)


# ========================
# Verify Route Calls
# ========================
booking_routes = Path(
    "app/booking/routes.py"
).read_text(
    encoding="utf-8"
)

admin_routes = Path(
    "app/admin/routes.py"
).read_text(
    encoding="utf-8"
)

checks = {
    "Create Booking email":
        "send_booking_created_email"
        in booking_routes,

    "Approve Booking email":
        "send_booking_approved_email"
        in admin_routes,

    "Reject Booking email":
        "send_booking_rejected_email"
        in admin_routes,

    "Admin Cancel email":
        "send_booking_cancelled_email"
        in admin_routes,
}

failed = [
    name
    for name, ok in checks.items()
    if not ok
]

if failed:
    print(
        "Integrasi route belum lengkap:"
    )

    for name in failed:
        print(
            f"- {name}"
        )

    sys.exit(1)


# ========================
# Verify No Applicant
# Cancel Email
# ========================
if (
    "def cancel_own_booking"
    in booking_routes
):
    own_cancel_block = (
        booking_routes.split(
            "def cancel_own_booking",
            1,
        )[1]
    )

    if (
        "send_booking_cancelled_email"
        in own_cancel_block
    ):
        print(
            "ERROR: Applicant self-cancel "
            "tidak sepatutnya menghantar email."
        )
        sys.exit(1)


print(
    "Phase 5D structural verification: OK"
)
