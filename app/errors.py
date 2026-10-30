from flask import render_template

from app.extensions import db


# ========================
# Register Error Handlers
# ========================
def register_error_handlers(app):

    # ========================
    # 403 Forbidden
    # ========================
    @app.errorhandler(403)
    def forbidden(error):
        return render_template(
            "errors/error.html",
            status_code=403,
            title="Akses Tidak Dibenarkan",
            message=(
                "Anda tidak mempunyai kebenaran "
                "untuk mengakses halaman ini."
            ),
        ), 403


    # ========================
    # 404 Not Found
    # ========================
    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            "errors/error.html",
            status_code=404,
            title="Halaman Tidak Ditemui",
            message=(
                "Halaman atau rekod yang diminta "
                "tidak dapat ditemui."
            ),
        ), 404


    # ========================
    # 429 Too Many Requests
    # ========================
    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template(
            "errors/error.html",
            status_code=429,
            title="Terlalu Banyak Percubaan",
            message=(
                "Terlalu banyak permintaan diterima. "
                "Sila cuba semula sebentar lagi."
            ),
        ), 429


    # ========================
    # 500 Internal Server Error
    # ========================
    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()

        original_error = getattr(
            error,
            "original_exception",
            error
        )

        app.logger.error(
            "Unhandled application error: %s",
            type(original_error).__name__
        )

        return render_template(
            "errors/error.html",
            status_code=500,
            title="Ralat Dalaman Pelayan",
            message=(
                "Sistem mengalami masalah semasa "
                "memproses permintaan anda. "
                "Sila cuba semula kemudian."
            ),
        ), 500