PHASE 5D - EMAIL NOTIFICATION COMPLETION PACKAGE
=================================================

Tujuan
------
Melengkapkan notifikasi email bagi:
1. Akaun activation
2. Booking created
3. Booking approved
4. Booking rejected
5. Booking cancelled oleh ADMIN
6. Applicant self-cancel TIDAK menghantar email
7. Email failure tidak menggagalkan transaksi booking
8. SMTP boleh kekal belum dikonfigurasi

Struktur pakej
--------------
phase5d_files/
  app/
    email.py
  tests/
    test_booking_email_messages.py
    test_booking_email_integrations.py

apply_phase5d_updates.py
verify_phase5d.py
run_phase5d_regression.ps1
.env.email.example
config_email_snippet.txt

PENTING
-------
Skrip apply_phase5d_updates.py TIDAK menggantikan routes.py.
Ia membuat backup dan hanya menyuntik import serta panggilan email
ke route semasa.

Backup yang dibuat:
- app/email.py.phase5d.bak
- app/booking/routes.py.phase5d.bak
- app/admin/routes.py.phase5d.bak

Cara guna
---------
1. Extract ZIP ke root projek:
   C:\laragon\www\meeting-room-booking

2. Pastikan folder berikut wujud selepas extract:
   phase5d_files\app
   phase5d_files\tests

3. Salin test:
   Copy-Item phase5d_files\tests\test_booking_email_messages.py tests\test_booking_email_messages.py -Force
   Copy-Item phase5d_files\tests\test_booking_email_integrations.py tests\test_booking_email_integrations.py -Force

4. Jalankan migrasi:
   python .\apply_phase5d_updates.py

5. Semak syntax:
   python -m py_compile app\email.py app\booking\routes.py app\admin\routes.py

6. Verify struktur:
   python .\verify_phase5d.py

7. Jalankan test email:
   python -m pytest tests/test_booking_email_messages.py tests/test_booking_email_integrations.py -v

   Sasaran:
   16 passed

8. Jalankan regression penuh:
   powershell.exe -ExecutionPolicy Bypass -File .\run_phase5d_regression.ps1

   Sasaran keseluruhan:
   35 passed

SMTP
----
SMTP sebenar masih boleh ditangguhkan.

send_email_safely() menggunakan:
MAIL_NOTIFICATIONS_ENABLED=False
sebagai nilai default jika config belum disediakan.

Jadi aplikasi tidak cuba menghantar email sebenar sehingga anda
mengaktifkannya.

Apabila BTM memberikan SMTP:
1. Rujuk .env.email.example
2. Tambah konfigurasi daripada config_email_snippet.txt ke Config
3. Isi maklumat SMTP sebenar
4. Tukar MAIL_NOTIFICATIONS_ENABLED=true
5. Uji pada staging dahulu

Reka bentuk pembatalan
----------------------
ADMIN cancel:
  email dihantar kepada pemohon.

Applicant self-cancel:
  tiada email dihantar.

Ini disengajakan mengikut keputusan projek.
