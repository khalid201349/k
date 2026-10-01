"""
برنامج الإجازات — تطبيق سطح مكتب (Windows)
يشتغل بدون إنترنت، البيانات تُخزَّن محلياً في قاعدة بيانات SQLite
داخل مجلد المستخدم (~/LeaveApp/leave_app.db).

لتحويله إلى ملف exe واحد:
    pyinstaller --onefile --windowed --name "برنامج الإجازات" leave_app_desktop.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from leave_logic import LeaveDB

APP_TITLE = "برنامج الإجازات"
BG = "#f6f7fb"
PRIMARY = "#1d4ed8"
PRIMARY_DARK = "#1e3a8a"
GREEN = "#15803d"
RED = "#b91c1c"
AMBER = "#b45309"
MUTED = "#6b7280"
CARD = "#ffffff"
BORDER = "#e5e9f2"

STATUS_LABELS = {"pending": "قيد الانتظار", "approved": "موافق عليها", "rejected": "مرفوضة"}
STATUS_COLORS = {"pending": AMBER, "approved": GREEN, "rejected": RED}


class LeaveApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("920x600")
        self.minsize(800, 540)
        self.configure(bg=BG)

        self.db = LeaveDB()
        self.current_user = None

        self._setup_styles()
        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10), background=CARD,
                         fieldbackground=CARD)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=(16, 8))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Login screen
    # ------------------------------------------------------------------
    def show_login(self):
        self.clear_container()
        self.current_user = None

        wrap = tk.Frame(self.container, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(wrap, bg=CARD, padx=40, pady=36, highlightbackground=BORDER,
                         highlightthickness=1)
        card.pack()

        tk.Label(card, text="📅", font=("Segoe UI Emoji", 28), bg=CARD).pack(pady=(0, 6))
        tk.Label(card, text=APP_TITLE, font=("Segoe UI", 16, "bold"), bg=CARD,
                 fg="#14213d").pack()
        tk.Label(card, text="سجّل دخولك لمتابعة طلبات إجازتك", font=("Segoe UI", 9),
                 bg=CARD, fg=MUTED).pack(pady=(2, 20))

        tk.Label(card, text="اسم المستخدم", font=("Segoe UI", 9), bg=CARD, fg=MUTED,
                 anchor="e").pack(fill="x")
        username_entry = ttk.Entry(card, width=30, font=("Segoe UI", 11), justify="right")
        username_entry.pack(pady=(4, 12), ipady=4)
        username_entry.focus()

        tk.Label(card, text="كلمة المرور", font=("Segoe UI", 9), bg=CARD, fg=MUTED,
                 anchor="e").pack(fill="x")
        password_entry = ttk.Entry(card, width=30, font=("Segoe UI", 11), show="•", justify="right")
        password_entry.pack(pady=(4, 6), ipady=4)

        error_label = tk.Label(card, text="", font=("Segoe UI", 9), bg=CARD, fg=RED)
        error_label.pack(pady=(4, 4))

        def do_login(event=None):
            user = self.db.authenticate(username_entry.get().strip(), password_entry.get())
            if not user:
                error_label.config(text="اسم المستخدم أو كلمة المرور غير صحيحة.")
                return
            self.current_user = user
            if user["role"] == "manager":
                self.show_manager_dashboard()
            else:
                self.show_employee_dashboard()

        password_entry.bind("<Return>", do_login)
        username_entry.bind("<Return>", lambda e: password_entry.focus())

        login_btn = tk.Button(card, text="دخول", font=("Segoe UI", 10, "bold"), bg=PRIMARY,
                               fg="white", activebackground=PRIMARY_DARK, bd=0, pady=9,
                               cursor="hand2", command=do_login)
        login_btn.pack(fill="x", pady=(14, 0))

        demo = tk.Frame(card, bg=CARD)
        demo.pack(fill="x", pady=(20, 0))
        tk.Frame(demo, bg=BORDER, height=1).pack(fill="x", pady=(0, 10))
        for label, creds in [("مدير", "manager / 1234"), ("موظفة", "sara / 1234"),
                              ("موظف", "khaled / 1234")]:
            row = tk.Frame(demo, bg=CARD)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=creds, font=("Consolas", 9), bg="#eef2ff", fg=PRIMARY_DARK,
                     padx=8, pady=2).pack(side="right")
            tk.Label(row, text=label, font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(side="right",
                                                                                      padx=(0, 8))

    # ------------------------------------------------------------------
    # Shared top bar
    # ------------------------------------------------------------------
    def build_topbar(self, subtitle):
        bar = tk.Frame(self.container, bg=PRIMARY, pady=14, padx=24)
        bar.pack(fill="x")

        left = tk.Frame(bar, bg=PRIMARY)
        left.pack(side="left")
        logout_btn = tk.Button(left, text="تسجيل الخروج", font=("Segoe UI", 9), bg=PRIMARY_DARK,
                                fg="white", bd=0, padx=12, pady=6, cursor="hand2",
                                command=self.show_login)
        logout_btn.pack()

        right = tk.Frame(bar, bg=PRIMARY)
        right.pack(side="right")
        tk.Label(right, text=subtitle, font=("Segoe UI", 13, "bold"), bg=PRIMARY,
                 fg="white").pack(anchor="e")
        tk.Label(right, text=self.current_user["name"], font=("Segoe UI", 9), bg=PRIMARY,
                 fg="#dbeafe").pack(anchor="e")

    # ------------------------------------------------------------------
    # Employee dashboard
    # ------------------------------------------------------------------
    def show_employee_dashboard(self):
        self.clear_container()
        self.build_topbar("لوحة الموظف")

        body = tk.Frame(self.container, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=BG)
        left.pack(side="right", fill="y", padx=(16, 0))
        right = tk.Frame(body, bg=BG)
        right.pack(side="right", fill="both", expand=True)

        # --- balance + new request card ---
        card = tk.Frame(left, bg=CARD, padx=20, pady=18, width=300, highlightbackground=BORDER,
                         highlightthickness=1)
        card.pack(fill="y")
        card.pack_propagate(False)

        remaining = self.db.remaining_days(self.current_user["id"])
        tk.Label(card, text="رصيدك المتبقي", font=("Segoe UI", 9), bg=CARD, fg=MUTED,
                 anchor="e").pack(fill="x")
        tk.Label(card, text=f"{remaining} يوم", font=("Segoe UI", 22, "bold"), bg=CARD,
                 fg=PRIMARY_DARK, anchor="e").pack(fill="x", pady=(0, 16))

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))
        tk.Label(card, text="طلب إجازة جديد", font=("Segoe UI", 11, "bold"), bg=CARD,
                 anchor="e").pack(fill="x", pady=(0, 10))

        tk.Label(card, text="من تاريخ (YYYY-MM-DD)", font=("Segoe UI", 9), bg=CARD, fg=MUTED,
                 anchor="e").pack(fill="x")
        start_entry = ttk.Entry(card, justify="right")
        start_entry.insert(0, date.today().isoformat())
        start_entry.pack(fill="x", pady=(2, 10), ipady=3)

        tk.Label(card, text="إلى تاريخ (YYYY-MM-DD)", font=("Segoe UI", 9), bg=CARD, fg=MUTED,
                 anchor="e").pack(fill="x")
        end_entry = ttk.Entry(card, justify="right")
        end_entry.insert(0, date.today().isoformat())
        end_entry.pack(fill="x", pady=(2, 10), ipady=3)

        tk.Label(card, text="السبب (اختياري)", font=("Segoe UI", 9), bg=CARD, fg=MUTED,
                 anchor="e").pack(fill="x")
        reason_text = tk.Text(card, height=3, font=("Segoe UI", 10), wrap="word")
        reason_text.pack(fill="x", pady=(2, 12))

        def submit():
            ok, msg = self.db.submit_request(
                self.current_user["id"], start_entry.get().strip(), end_entry.get().strip(),
                reason_text.get("1.0", "end").strip()
            )
            if ok:
                messagebox.showinfo("تم", msg)
                self.show_employee_dashboard()
            else:
                messagebox.showerror("خطأ", msg)

        tk.Button(card, text="إرسال الطلب", font=("Segoe UI", 10, "bold"), bg=PRIMARY,
                  fg="white", bd=0, pady=9, cursor="hand2", command=submit).pack(fill="x")

        # --- requests table ---
        tk.Label(right, text="طلباتي", font=("Segoe UI", 12, "bold"), bg=BG,
                 anchor="e").pack(fill="x", pady=(0, 8))

        columns = ("dates", "days", "reason", "status")
        tree = ttk.Treeview(right, columns=columns, show="headings", height=16)
        tree.heading("dates", text="التواريخ")
        tree.heading("days", text="الأيام")
        tree.heading("reason", text="السبب")
        tree.heading("status", text="الحالة")
        tree.column("dates", width=190, anchor="center")
        tree.column("days", width=70, anchor="center")
        tree.column("reason", width=260, anchor="e")
        tree.column("status", width=120, anchor="center")
        tree.pack(fill="both", expand=True)

        for tag, color in STATUS_COLORS.items():
            tree.tag_configure(tag, foreground=color)

        requests = self.db.get_requests_for_user(self.current_user["id"])
        if not requests:
            tree.insert("", "end", values=("لا يوجد طلبات بعد", "", "", ""))
        for r in requests:
            tree.insert("", "end", values=(
                f"{r['start_date']} → {r['end_date']}", r["days"], r["reason"] or "—",
                STATUS_LABELS[r["status"]]
            ), tags=(r["status"],))

    # ------------------------------------------------------------------
    # Manager dashboard
    # ------------------------------------------------------------------
    def show_manager_dashboard(self, status_filter="pending"):
        self.clear_container()
        self.build_topbar("لوحة المدير")

        body = tk.Frame(self.container, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        # filter chips
        filters = tk.Frame(body, bg=BG)
        filters.pack(fill="x", pady=(0, 10))
        pending_n = self.db.pending_count()
        for key, label in [("pending", f"قيد الانتظار ({pending_n})"), ("approved", "موافق عليها"),
                            ("rejected", "مرفوضة"), ("all", "الكل")]:
            is_active = key == status_filter
            btn = tk.Button(
                filters, text=label, font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=PRIMARY if is_active else "white", fg="white" if is_active else MUTED,
                bd=1, relief="solid", padx=14, pady=6, cursor="hand2",
                command=lambda k=key: self.show_manager_dashboard(k)
            )
            btn.pack(side="right", padx=(8, 0))

        columns = ("employee", "dates", "days", "reason", "status")
        tree = ttk.Treeview(body, columns=columns, show="headings", height=16)
        tree.heading("employee", text="الموظف")
        tree.heading("dates", text="التواريخ")
        tree.heading("days", text="الأيام")
        tree.heading("reason", text="السبب")
        tree.heading("status", text="الحالة")
        tree.column("employee", width=140, anchor="e")
        tree.column("dates", width=190, anchor="center")
        tree.column("days", width=70, anchor="center")
        tree.column("reason", width=240, anchor="e")
        tree.column("status", width=110, anchor="center")
        tree.pack(fill="both", expand=True, pady=(0, 10))

        for tag, color in STATUS_COLORS.items():
            tree.tag_configure(tag, foreground=color)

        requests = self.db.get_all_requests(status_filter)
        id_by_row = {}
        if not requests:
            tree.insert("", "end", values=("لا توجد طلبات في هذا التصنيف", "", "", "", ""))
        for r in requests:
            row_id = tree.insert("", "end", values=(
                r["employee_name"], f"{r['start_date']} → {r['end_date']}", r["days"],
                r["reason"] or "—", STATUS_LABELS[r["status"]]
            ), tags=(r["status"],))
            id_by_row[row_id] = r

        # action buttons for the selected (pending) request
        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x")

        def get_selected_request():
            sel = tree.selection()
            if not sel or sel[0] not in id_by_row:
                return None
            return id_by_row[sel[0]]

        def approve():
            req = get_selected_request()
            if not req or req["status"] != "pending":
                messagebox.showwarning("تنبيه", "اختر طلباً قيد الانتظار أولاً.")
                return
            self.db.decide_request(req["id"], "approved")
            self.show_manager_dashboard(status_filter)

        def reject():
            req = get_selected_request()
            if not req or req["status"] != "pending":
                messagebox.showwarning("تنبيه", "اختر طلباً قيد الانتظار أولاً.")
                return
            self.db.decide_request(req["id"], "rejected")
            self.show_manager_dashboard(status_filter)

        tk.Button(actions, text="قبول الطلب المحدد", font=("Segoe UI", 9, "bold"), bg=GREEN,
                  fg="white", bd=0, padx=14, pady=8, cursor="hand2",
                  command=approve).pack(side="right", padx=(8, 0))
        tk.Button(actions, text="رفض الطلب المحدد", font=("Segoe UI", 9, "bold"), bg=RED,
                  fg="white", bd=0, padx=14, pady=8, cursor="hand2",
                  command=reject).pack(side="right")
        tk.Label(actions, text="اختر صفاً من الجدول أعلاه ثم اضغط قبول أو رفض",
                 font=("Segoe UI", 8), bg=BG, fg=MUTED).pack(side="left")


if __name__ == "__main__":
    app = LeaveApp()
    app.mainloop()
