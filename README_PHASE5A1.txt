PHASE 5A.1 - TEST ENVIRONMENT

1. Copy into the project root:
   pytest.ini
   requirements-dev.txt
   tests/

2. Activate the existing virtual environment.

3. Install development test dependency:
   pip install -r requirements-dev.txt

4. Run:
   python -m pytest -v

Expected initial coverage:
- isolated in-memory SQLite test database
- password hash smoke test
- booking fixture smoke test
- APPROVED booking overlap conflict
- PENDING booking does not lock slot
- adjacent bookings are allowed
- exclude_booking_id avoids self-conflict
- APPROVED past booking -> COMPLETED
- PENDING past booking -> EXPIRED
- future booking remains unchanged

Important:
The test database uses sqlite:// (in-memory). It does not use instance/meeting_room.db.
