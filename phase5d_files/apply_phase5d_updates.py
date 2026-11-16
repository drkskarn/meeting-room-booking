from pathlib import Path
import shutil
import re
import sys


ROOT = Path.cwd()

BOOKING_ROUTES = (
    ROOT / "app" / "booking" / "routes.py"
)

ADMIN_ROUTES = (
    ROOT / "app" / "admin" / "routes.py"
)

EMAIL_FILE = (
    ROOT / "app" / "email.py"
)

PACKAGE_EMAIL_FILE = (
    ROOT / "phase5d_files" / "app" / "email.py"
)


# ========================
# Backup
# ========================
def backup(path):
    backup_path = path.with_suffix(
        path.suffix + ".phase5d.bak"
    )

    shutil.copy2(
        path,
        backup_path,
    )

    print(
        f"Backup: {backup_path}"
    )


# ========================
# Function Block
# ========================
def get_function_block(
    content,
    function_name,
):
    pattern = re.compile(
        rf"(?ms)^def {re.escape(function_name)}"
        rf"\([^)]*\):.*?"
        rf"(?=^@|^def |\Z)"
    )

    match = pattern.search(
        content
    )

    if match is None:
        raise RuntimeError(
            f"Function {function_name} "
            "tidak dijumpai."
        )

    return (
        match.start(),
        match.end(),
        match.group(0),
    )


# ========================
# Add Import
# ========================
def ensure_import(
    content,
    import_block,
):
    marker = (
        "from app.email import ("
    )

    if marker in content:
        return content

    anchor = (
        "from app.extensions import db"
    )

    if anchor not in content:
        raise RuntimeError(
            "Import anchor "
            "'from app.extensions import db' "
            "tidak dijumpai."
        )

    return content.replace(
        anchor,
        anchor
        + "\n\n"
        + import_block,
        1,
    )


# ========================
# Inject After Commit
# ========================
def inject_after_commit(
    content,
    function_name,
    marker,
    snippet,
):
    start, end, block = (
        get_function_block(
            content,
            function_name,
        )
    )

    if marker in block:
        print(
            f"{function_name}: "
            "email integration sudah ada."
        )
        return content

    commit = (
        "    db.session.commit()"
    )

    position = block.rfind(
        commit
    )

    if position == -1:
        raise RuntimeError(
            f"{function_name}: "
            "db.session.commit() "
            "tidak dijumpai."
        )

    insertion_point = (
        position
        + len(commit)
    )

    new_block = (
        block[:insertion_point]
        + "\n\n"
        + snippet
        + block[insertion_point:]
    )

    return (
        content[:start]
        + new_block
        + content[end:]
    )


# ========================
# Replace email.py
# ========================
if not PACKAGE_EMAIL_FILE.exists():
    raise RuntimeError(
        "Fail phase5d_files/app/email.py "
        "tidak dijumpai."
    )

if EMAIL_FILE.exists():
    backup(
        EMAIL_FILE
    )

shutil.copy2(
    PACKAGE_EMAIL_FILE,
    EMAIL_FILE,
)

print(
    "Dikemaskini: app/email.py"
)


# ========================
# Booking Routes
# ========================
booking_content = (
    BOOKING_ROUTES
    .read_text(
        encoding="utf-8"
    )
)

backup(
    BOOKING_ROUTES
)

booking_import = """from app.email import (
    send_booking_created_email,
    send_email_safely,
)"""

booking_content = ensure_import(
    booking_content,
    booking_import,
)

booking_snippet = """    # ========================
    # Email - Booking Created
    # ========================
    send_email_safely(
        send_booking_created_email,
        booking,
    )"""

booking_content = inject_after_commit(
    booking_content,
    "create_booking",
    "send_booking_created_email",
    booking_snippet,
)

BOOKING_ROUTES.write_text(
    booking_content,
    encoding="utf-8",
)

print(
    "Dikemaskini: "
    "app/booking/routes.py"
)


# ========================
# Admin Routes
# ========================
admin_content = (
    ADMIN_ROUTES
    .read_text(
        encoding="utf-8"
    )
)

backup(
    ADMIN_ROUTES
)

admin_import = """from app.email import (
    send_booking_approved_email,
    send_booking_cancelled_email,
    send_booking_rejected_email,
    send_email_safely,
)"""

admin_content = ensure_import(
    admin_content,
    admin_import,
)

approved_snippet = """    # ========================
    # Email - Booking Approved
    # ========================
    send_email_safely(
        send_booking_approved_email,
        booking,
    )"""

rejected_snippet = """        # ========================
        # Email - Booking Rejected
        # ========================
        send_email_safely(
            send_booking_rejected_email,
            booking,
        )"""

cancelled_snippet = """        # ========================
        # Email - Admin Cancelled
        # ========================
        send_email_safely(
            send_booking_cancelled_email,
            booking,
        )"""

admin_content = inject_after_commit(
    admin_content,
    "approve_booking",
    "send_booking_approved_email",
    approved_snippet,
)

admin_content = inject_after_commit(
    admin_content,
    "reject_booking",
    "send_booking_rejected_email",
    rejected_snippet,
)

admin_content = inject_after_commit(
    admin_content,
    "cancel_booking",
    "send_booking_cancelled_email",
    cancelled_snippet,
)

ADMIN_ROUTES.write_text(
    admin_content,
    encoding="utf-8",
)

print(
    "Dikemaskini: "
    "app/admin/routes.py"
)

print()
print(
    "Phase 5D route patch selesai."
)
print(
    "Applicant self-cancel route "
    "tidak diubah."
)
