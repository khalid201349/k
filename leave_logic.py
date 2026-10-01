"""
Core data/business logic for the Leave Management desktop app.
No GUI dependencies here on purpose, so this module can be tested
and reused independently of Tkinter.
"""
import os
import sqlite3
from datetime import datetime, date

DEFAULT_BALANCE = 21


def default_db_path():
    """Where the database lives once the app is installed/packaged.

    Using the user's home folder (not the install folder) means the app
    keeps working even when packaged as a read-only .exe.
    """
    folder = os.path.join(os.path.expanduser("~"), "LeaveApp")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "leave_app.db")


class LeaveDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or default_db_path()
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        conn = self._connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('employee', 'manager')),
                annual_balance INTEGER NOT NULL DEFAULT 21
            );
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                days INTEGER NOT NULL,
                reason TEXT,
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO users (name, username, password, role, annual_balance) VALUES (?,?,?,?,?)",
                [
                    ("أحمد المدير", "manager", "1234", "manager", DEFAULT_BALANCE),
                    ("سارة الموظفة", "sara", "1234", "employee", DEFAULT_BALANCE),
                    ("خالد الموظف", "khaled", "1234", "employee", DEFAULT_BALANCE),
                ],
            )
        conn.commit()
        conn.close()

    # -- auth -----------------------------------------------------------
    def authenticate(self, username, password):
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    # -- employees --------------------------------------------------------
    def list_employees(self):
        conn = self._connect()
        rows = conn.execute("SELECT * FROM users WHERE role='employee' ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_user(self, user_id):
        conn = self._connect()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    # -- leave requests ---------------------------------------------------
    @staticmethod
    def calc_days(start_str, end_str):
        s = datetime.strptime(start_str, "%Y-%m-%d").date()
        e = datetime.strptime(end_str, "%Y-%m-%d").date()
        return (e - s).days + 1

    def used_days(self, user_id):
        conn = self._connect()
        row = conn.execute(
            "SELECT COALESCE(SUM(days),0) AS used FROM leave_requests "
            "WHERE user_id=? AND status='approved'",
            (user_id,),
        ).fetchone()
        conn.close()
        return row["used"]

    def remaining_days(self, user_id):
        user = self.get_user(user_id)
        if not user:
            return 0
        return user["annual_balance"] - self.used_days(user_id)

    def submit_request(self, user_id, start_date, end_date, reason):
        """Returns (success: bool, message: str)."""
        try:
            days = self.calc_days(start_date, end_date)
        except (ValueError, TypeError):
            return False, "الرجاء إدخال تواريخ صحيحة بصيغة YYYY-MM-DD."
        if days <= 0:
            return False, "تاريخ النهاية يجب أن يكون بعد أو يساوي تاريخ البداية."

        remaining = self.remaining_days(user_id)
        if days > remaining:
            return False, f"لا يوجد رصيد كافٍ. رصيدك المتبقي {remaining} يوم فقط."

        conn = self._connect()
        conn.execute(
            "INSERT INTO leave_requests (user_id, start_date, end_date, days, reason, status, created_at) "
            "VALUES (?,?,?,?,?,'pending',?)",
            (user_id, start_date, end_date, days, reason, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        conn.close()
        return True, "تم إرسال طلب الإجازة بنجاح."

    def get_requests_for_user(self, user_id):
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM leave_requests WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_requests(self, status_filter=None):
        conn = self._connect()
        query = (
            "SELECT lr.*, u.name AS employee_name FROM leave_requests lr "
            "JOIN users u ON lr.user_id = u.id"
        )
        params = ()
        if status_filter and status_filter != "all":
            query += " WHERE lr.status = ?"
            params = (status_filter,)
        query += " ORDER BY lr.created_at DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def decide_request(self, request_id, decision):
        if decision not in ("approved", "rejected"):
            return False, "إجراء غير صالح."
        conn = self._connect()
        conn.execute("UPDATE leave_requests SET status=? WHERE id=?", (decision, request_id))
        conn.commit()
        conn.close()
        return True, "تم تحديث حالة الطلب."

    def pending_count(self):
        conn = self._connect()
        n = conn.execute("SELECT COUNT(*) FROM leave_requests WHERE status='pending'").fetchone()[0]
        conn.close()
        return n
