# from flask import request, jsonify, session, render_template, redirect
# from db import mysql
# from auth import login_user
# from rbac import is_admin, is_student, is_staff
# from logging_utils import log_action


# # ─────────────────────────────────────────────
# #  Helpers
# # ─────────────────────────────────────────────
# def require_login():
#     if 'username' not in session:
#         return redirect('/login')
#     return None


# def require_admin():
#     if session.get('role') != 'Admin':
#         return jsonify({'error': 'Unauthorized'}), 403
#     return None


# # ─────────────────────────────────────────────
# #  Route registration
# # ─────────────────────────────────────────────
# def register_routes(app):

#     # ── Home ──────────────────────────────────
#     @app.route('/')
#     def home():
#         return redirect('/login')

#     # ── LOGIN ─────────────────────────────────
#     @app.route('/login', methods=['GET', 'POST'])
#     def login():
#         if request.method == 'POST':
#             username = request.form['username']
#             password = request.form['password']
#             user = login_user(username, password)

#             if user:
#                 session['username']    = username
#                 session['role']        = user['role']         # 'Admin' | 'User'
#                 session['member_id']   = user['member_id']    # int | None
#                 session['member_role'] = user['member_role']  # 'Student' | 'Staff' | 'Admin'
#                 session['sub_id']      = user['sub_id']       # StudentID | StaffID | None
#                 log_action('Login', username)
#                 return redirect('/dashboard')
#             else:
#                 return render_template('login.html', error='Invalid credentials')

#         return render_template('login.html', error=None)

#     # ── LOGOUT ────────────────────────────────
#     @app.route('/logout')
#     def logout():
#         log_action('Logout', session.get('username', 'unknown'))
#         session.clear()
#         return redirect('/login')

#     # ── SIGNUP ────────────────────────────────
#     @app.route('/signup', methods=['GET', 'POST'])
#     def signup():
#         if request.method == 'POST':
#             d = request.form
#             cur = mysql.connection.cursor()

#             try:
#                 # ── 1. Derive username from email ──────────
#                 username = d['email'].split('@')[0]

#                 # ── 2. Check for duplicate username / email ─
#                 cur.execute("SELECT COUNT(*) FROM Users WHERE username=%s", (username,))
#                 if cur.fetchone()[0] > 0:
#                     return render_template('signup.html',
#                                            error='Username already exists. Use a different email.')

#                 cur.execute("SELECT COUNT(*) FROM Member WHERE Email=%s", (d['email'],))
#                 if cur.fetchone()[0] > 0:
#                     return render_template('signup.html',
#                                            error='Email already registered.')

#                 # ── 3. Get next MemberID ───────────────────
#                 cur.execute("SELECT COALESCE(MAX(MemberID), 0) + 1 FROM Member")
#                 member_id = cur.fetchone()[0]

#                 # ── 4. Insert into Member ──────────────────
#                 cur.execute(
#                     "INSERT INTO Member (MemberID, Name, DOB, Email, ContactNumber, Role) "
#                     "VALUES (%s, %s, %s, %s, %s, %s)",
#                     (member_id, d['name'], d['dob'], d['email'],
#                      d['contact'], d['member_role'])
#                 )

#                 # ── 5. Insert into Student or Staff ────────
#                 if d['member_role'] == 'Student':
#                     cur.execute("SELECT COALESCE(MAX(StudentID), 23110000) + 1 FROM Student")
#                     student_id = cur.fetchone()[0]
#                     cur.execute(
#                         "INSERT INTO Student (StudentID, MemberID, HostelBlock, RoomNo, Program) "
#                         "VALUES (%s, %s, %s, %s, %s)",
#                         (student_id, member_id,
#                          d['hostel_block'], d['room_no'], d['program'])
#                     )

#                 elif d['member_role'] == 'Staff':
#                     cur.execute("SELECT COALESCE(MAX(StaffID), 200) + 1 FROM Staff")
#                     staff_id = cur.fetchone()[0]
#                     cur.execute(
#                         "INSERT INTO Staff (StaffID, MemberID, JobRole, Salary, HireDate) "
#                         "VALUES (%s, %s, %s, %s, CURDATE())",
#                         (staff_id, member_id, d['job_role'], d['salary'])
#                     )

#                 # ── 6. Insert into Users ───────────────────
#                 cur.execute(
#                     "INSERT INTO Users (username, password, role) VALUES (%s, %s, 'User')",
#                     (username, d['password'])
#                 )

#                 mysql.connection.commit()
#                 log_action(f"New signup: {username} ({d['member_role']})", username)
#                 return render_template('login.html',
#                                        error=None,
#                                        success=f"Account created! Your username is '{username}'. Please log in.")

#             except Exception as e:
#                 mysql.connection.rollback()
#                 return render_template('signup.html',
#                                        error=f"Signup failed: {str(e)}")
#             finally:
#                 cur.close()

#         return render_template('signup.html', error=None)

#     # ─────────────────────────────────────────
#     #  DASHBOARD  (role-aware landing page)
#     # ─────────────────────────────────────────
#     @app.route('/dashboard')
#     def dashboard():
#         redir = require_login()
#         if redir:
#             return redir

#         role        = session.get('role')
#         member_role = session.get('member_role')   # 'Admin' | 'Student' | 'Staff'
#         member_id   = session.get('member_id')
#         cur         = mysql.connection.cursor()

#         # ── Admin dashboard ──
#         if is_admin(role):
#             cur.execute("SELECT COUNT(*) FROM Member")
#             total_members = cur.fetchone()[0]

#             cur.execute("SELECT COUNT(*) FROM Student")
#             total_students = cur.fetchone()[0]

#             cur.execute("SELECT COUNT(*) FROM Staff")
#             total_staff = cur.fetchone()[0]

#             cur.execute("SELECT COUNT(*) FROM MonthlyMessPayment WHERE Status='Pending'")
#             pending_bills = cur.fetchone()[0]

#             cur.execute("SELECT COALESCE(SUM(TotalCost),0) FROM Purchase")
#             total_expense = cur.fetchone()[0]

#             cur.execute(
#                 "SELECT Name, StockQty, Unit, MinStockLevel "
#                 "FROM Inventory WHERE StockQty <= ReorderLevel"
#             )
#             low_stock = cur.fetchall()

#             cur.close()
#             return render_template(
#                 'dashboard_admin.html',
#                 role=role, member_role=member_role,
#                 total_members=total_members,
#                 total_students=total_students,
#                 total_staff=total_staff,
#                 pending_bills=pending_bills,
#                 total_expense=total_expense,
#                 low_stock=low_stock
#             )

#         # ── Student dashboard ──
#         elif is_student(member_role):
#             cur.execute(
#                 """
#                 SELECT m.Name, m.DOB, m.Email, m.ContactNumber,
#                        s.HostelBlock, s.RoomNo, s.Program, s.StudentID
#                 FROM Member m
#                 JOIN Student s ON m.MemberID = s.MemberID
#                 WHERE m.MemberID = %s
#                 """,
#                 (member_id,)
#             )
#             profile = cur.fetchone()

#             cur.execute(
#                 """
#                 SELECT StartDate, EndDate, Amount, Status
#                 FROM MonthlyMessPayment
#                 WHERE MemberID = %s
#                 ORDER BY StartDate DESC LIMIT 6
#                 """,
#                 (member_id,)
#             )
#             payments = cur.fetchall()

#             cur.execute(
#                 """
#                 SELECT ds.MealDate, ds.MealType, ml.Status
#                 FROM MealLog ml
#                 JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
#                 WHERE ml.MemberID = %s
#                 ORDER BY ds.MealDate DESC LIMIT 10
#                 """,
#                 (member_id,)
#             )
#             meal_logs = cur.fetchall()

#             cur.close()
#             return render_template(
#                 'dashboard_student.html',
#                 role=role, member_role=member_role,
#                 profile=profile,
#                 payments=payments,
#                 meal_logs=meal_logs
#             )

#         # ── Staff dashboard ──
#         elif is_staff(member_role):
#             cur.execute(
#                 """
#                 SELECT m.Name, m.DOB, m.Email, m.ContactNumber,
#                        st.JobRole, st.Salary, st.HireDate, st.StaffID
#                 FROM Member m
#                 JOIN Staff st ON m.MemberID = st.MemberID
#                 WHERE m.MemberID = %s
#                 """,
#                 (member_id,)
#             )
#             profile = cur.fetchone()

#             cur.execute(
#                 """
#                 SELECT ShiftDate, ShiftType, CheckInTime, CheckOutTime, TotalHours
#                 FROM StaffShiftLog
#                 WHERE StaffID = (SELECT StaffID FROM Staff WHERE MemberID = %s)
#                 ORDER BY ShiftDate DESC LIMIT 10
#                 """,
#                 (member_id,)
#             )
#             shifts = cur.fetchall()

#             cur.close()
#             return render_template(
#                 'dashboard_staff.html',
#                 role=role, member_role=member_role,
#                 profile=profile,
#                 shifts=shifts
#             )

#         cur.close()
#         return "Unknown role", 400

#     # ─────────────────────────────────────────
#     #  MEMBERS
#     # ─────────────────────────────────────────
#     @app.route('/members')
#     def view_members():
#         redir = require_login()
#         if redir:
#             return redir

#         cur = mysql.connection.cursor()
#         if is_admin(session.get('role')):
#             cur.execute("SELECT * FROM Member ORDER BY MemberID")
#         else:
#             cur.execute(
#                 "SELECT * FROM Member WHERE MemberID = %s",
#                 (session.get('member_id'),)
#             )
#         members = cur.fetchall()
#         cur.close()
#         return render_template('members.html', members=members,
#                                role=session['role'],
#                                member_role=session.get('member_role'))

#     # ─────────────────────────────────────────
#     #  FUNCTIONALITY 1 — Meal Attendance
#     # ─────────────────────────────────────────
#     @app.route('/meal_attendance')
#     def meal_attendance():
#         redir = require_login()
#         if redir:
#             return redir

#         cur = mysql.connection.cursor()

#         if is_admin(session.get('role')):
#             cur.execute(
#                 """
#                 SELECT ds.MealDate, ds.MealType, ml.Status, COUNT(*) AS Total
#                 FROM MealLog ml
#                 JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
#                 GROUP BY ds.MealDate, ds.MealType, ml.Status
#                 ORDER BY ds.MealDate DESC,
#                          FIELD(ds.MealType,'Breakfast','Lunch','Snacks','Dinner')
#                 """
#             )
#             data = cur.fetchall()
#             cur.close()
#             return render_template('meal_attendance.html', data=data,
#                                    role=session['role'], view='admin')
#         else:
#             cur.execute(
#                 """
#                 SELECT ds.MealDate, ds.MealType, ml.Status
#                 FROM MealLog ml
#                 JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
#                 WHERE ml.MemberID = %s
#                 ORDER BY ds.MealDate DESC
#                 """,
#                 (session.get('member_id'),)
#             )
#             data = cur.fetchall()
#             cur.close()
#             return render_template('meal_attendance.html', data=data,
#                                    role=session['role'], view='student')

#     # ─────────────────────────────────────────
#     #  FUNCTIONALITY 2 — Menu Planning
#     # ─────────────────────────────────────────
#     @app.route('/menu')
#     def menu():
#         redir = require_login()
#         if redir:
#             return redir

#         date = request.args.get('date', '')
#         cur  = mysql.connection.cursor()

#         if date:
#             cur.execute(
#                 """
#                 SELECT ds.MealDate, ds.MealType, mi.Name, mi.Category,
#                        si.QuantityPrepared, si.Unit
#                 FROM DailySchedule ds
#                 JOIN Schedule_Items si ON ds.ScheduleID = si.ScheduleID
#                 JOIN MenuItem mi       ON si.ItemID     = mi.ItemID
#                 WHERE ds.MealDate = %s
#                 ORDER BY FIELD(ds.MealType,'Breakfast','Lunch','Snacks','Dinner')
#                 """,
#                 (date,)
#             )
#         else:
#             cur.execute(
#                 """
#                 SELECT ds.MealDate, ds.MealType, mi.Name, mi.Category,
#                        si.QuantityPrepared, si.Unit
#                 FROM DailySchedule ds
#                 JOIN Schedule_Items si ON ds.ScheduleID = si.ScheduleID
#                 JOIN MenuItem mi       ON si.ItemID     = mi.ItemID
#                 ORDER BY ds.MealDate DESC,
#                          FIELD(ds.MealType,'Breakfast','Lunch','Snacks','Dinner')
#                 LIMIT 40
#                 """
#             )

#         data = cur.fetchall()
#         cur.close()
#         return render_template('menu.html', data=data, role=session['role'],
#                                member_role=session.get('member_role'),
#                                selected_date=date)

#     @app.route('/menu/add', methods=['POST'])
#     def menu_add():
#         err = require_admin()
#         if err:
#             return err

#         d   = request.form
#         cur = mysql.connection.cursor()

#         cur.execute(
#             "SELECT ScheduleID FROM DailySchedule WHERE MealDate=%s AND MealType=%s",
#             (d['MealDate'], d['MealType'])
#         )
#         row = cur.fetchone()
#         if row:
#             schedule_id = row[0]
#         else:
#             cur.execute(
#                 "INSERT INTO DailySchedule (ScheduleID, MealDate, MealType, IsActive) "
#                 "VALUES (%s, %s, %s, TRUE)",
#                 (d['ScheduleID'], d['MealDate'], d['MealType'])
#             )
#             schedule_id = d['ScheduleID']

#         cur.execute(
#             "INSERT INTO Schedule_Items (ScheduleID, ItemID, QuantityPrepared, Unit) "
#             "VALUES (%s, %s, %s, %s)",
#             (schedule_id, d['ItemID'], d['QuantityPrepared'], d['Unit'])
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Menu item {d['ItemID']} added to schedule {schedule_id}", session['username'])
#         return redirect('/menu')

#     # ─────────────────────────────────────────
#     #  FUNCTIONALITY 3 — Monthly Billing
#     # ─────────────────────────────────────────
#     @app.route('/billing')
#     def billing():
#         redir = require_login()
#         if redir:
#             return redir

#         cur = mysql.connection.cursor()

#         if is_admin(session.get('role')):
#             cur.execute(
#                 """
#                 SELECT m.Name, mp.StartDate, mp.EndDate, mp.Amount,
#                        mp.Status, mp.MonthlyPaymentID
#                 FROM MonthlyMessPayment mp
#                 JOIN Member m ON mp.MemberID = m.MemberID
#                 ORDER BY mp.Status DESC, mp.StartDate DESC
#                 """
#             )
#             data = cur.fetchall()
#             cur.close()
#             return render_template('billing.html', data=data,
#                                    role=session['role'], view='admin')
#         else:
#             cur.execute(
#                 """
#                 SELECT StartDate, EndDate, Amount, Status
#                 FROM MonthlyMessPayment
#                 WHERE MemberID = %s
#                 ORDER BY StartDate DESC
#                 """,
#                 (session.get('member_id'),)
#             )
#             data = cur.fetchall()
#             cur.close()
#             return render_template('billing.html', data=data,
#                                    role=session['role'], view='student')

#     @app.route('/billing/update_status', methods=['POST'])
#     def billing_update_status():
#         err = require_admin()
#         if err:
#             return err

#         pid    = request.form['payment_id']
#         status = request.form['status']
#         cur    = mysql.connection.cursor()
#         cur.execute(
#             "UPDATE MonthlyMessPayment SET Status=%s WHERE MonthlyPaymentID=%s",
#             (status, pid)
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Billing status updated: payment {pid} -> {status}", session['username'])
#         return redirect('/billing')

#     # ─────────────────────────────────────────
#     #  FUNCTIONALITY 4 — Inventory
#     # ─────────────────────────────────────────
#     @app.route('/inventory')
#     def inventory():
#         redir = require_login()
#         if redir:
#             return redir

#         cur = mysql.connection.cursor()
#         cur.execute(
#             """
#             SELECT IngredientID, Name, StockQty, Unit,
#                    MinStockLevel, ReorderLevel, LastUpdated,
#                    CASE
#                        WHEN StockQty <= MinStockLevel THEN 'Critical'
#                        WHEN StockQty <= ReorderLevel  THEN 'Low'
#                        ELSE 'OK'
#                    END AS StockStatus
#             FROM Inventory
#             ORDER BY StockQty ASC
#             """
#         )
#         data = cur.fetchall()
#         cur.close()
#         return render_template('inventory.html', data=data, role=session['role'],
#                                member_role=session.get('member_role'))

#     @app.route('/inventory/update', methods=['POST'])
#     def inventory_update():
#         err = require_admin()
#         if err:
#             return err

#         d   = request.form
#         cur = mysql.connection.cursor()
#         cur.execute(
#             """
#             UPDATE Inventory
#             SET StockQty=%s, MinStockLevel=%s, ReorderLevel=%s, LastUpdated=CURDATE()
#             WHERE IngredientID=%s
#             """,
#             (d['StockQty'], d['MinStockLevel'], d['ReorderLevel'], d['IngredientID'])
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Inventory updated: ingredient {d['IngredientID']}", session['username'])
#         return redirect('/inventory')

#     # ─────────────────────────────────────────
#     #  FUNCTIONALITY 5 — Suppliers & Expenses
#     # ─────────────────────────────────────────
#     @app.route('/suppliers')
#     def suppliers():
#         redir = require_login()
#         if redir:
#             return redir

#         err = require_admin()
#         if err:
#             return err

#         cur = mysql.connection.cursor()
#         cur.execute(
#             """
#             SELECT s.SupplierID, s.CompanyName, s.ContactName, s.Phone,
#                    s.SupplierType, COALESCE(SUM(p.TotalCost), 0) AS TotalSpent
#             FROM Supplier s
#             LEFT JOIN Purchase p ON s.SupplierID = p.SupplierID
#             GROUP BY s.SupplierID
#             ORDER BY TotalSpent DESC
#             """
#         )
#         suppliers_data = cur.fetchall()

#         cur.execute(
#             """
#             SELECT p.PurchaseID, s.CompanyName, i.Name AS Ingredient,
#                    p.Quantity, p.UnitPrice, p.TotalCost, p.PurchaseDate
#             FROM Purchase p
#             JOIN Supplier s  ON p.SupplierID   = s.SupplierID
#             JOIN Inventory i ON p.IngredientID = i.IngredientID
#             ORDER BY p.PurchaseDate DESC
#             LIMIT 20
#             """
#         )
#         purchases = cur.fetchall()
#         cur.close()

#         return render_template('suppliers.html', suppliers=suppliers_data,
#                                purchases=purchases, role=session['role'])

#     # ─────────────────────────────────────────
#     #  FUNCTIONALITY 6 — Food Waste
#     # ─────────────────────────────────────────
#     @app.route('/waste')
#     def waste():
#         redir = require_login()
#         if redir:
#             return redir

#         err = require_admin()
#         if err:
#             return err

#         cur = mysql.connection.cursor()
#         cur.execute(
#             """
#             SELECT ds.MealDate, ds.MealType,
#                    w.WasteQty_Kg, w.Waste_category, w.RecordedDate
#             FROM WasteLog w
#             JOIN DailySchedule ds ON w.ScheduleID = ds.ScheduleID
#             ORDER BY w.RecordedDate DESC
#             """
#         )
#         data = cur.fetchall()

#         cur.execute(
#             """
#             SELECT Waste_category, SUM(WasteQty_Kg) AS Total
#             FROM WasteLog
#             GROUP BY Waste_category
#             """
#         )
#         totals = cur.fetchall()
#         cur.close()

#         return render_template('waste.html', data=data, totals=totals,
#                                role=session['role'])

#     @app.route('/waste/add', methods=['POST'])
#     def waste_add():
#         err = require_admin()
#         if err:
#             return err

#         d   = request.form
#         cur = mysql.connection.cursor()
#         cur.execute(
#             """
#             INSERT INTO WasteLog (WasteID, ScheduleID, WasteQty_Kg, Waste_category, RecordedDate)
#             VALUES (%s, %s, %s, %s, CURDATE())
#             """,
#             (d['WasteID'], d['ScheduleID'], d['WasteQty_Kg'], d['Waste_category'])
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Waste logged for schedule {d['ScheduleID']}", session['username'])
#         return redirect('/waste')

#     # ─────────────────────────────────────────
#     #  FUNCTIONALITY 7 — Meal Ratings
#     # ─────────────────────────────────────────
#     @app.route('/ratings')
#     def ratings():
#         redir = require_login()
#         if redir:
#             return redir

#         cur = mysql.connection.cursor()
#         cur.execute(
#             """
#             SELECT ds.MealDate, ds.MealType,
#                    ROUND(AVG(mr.Rating), 2) AS AvgRating,
#                    COUNT(mr.RatingID)       AS TotalRatings,
#                    MIN(mr.Rating)           AS MinRating,
#                    MAX(mr.Rating)           AS MaxRating
#             FROM MessRating mr
#             JOIN DailySchedule ds ON mr.ScheduleID = ds.ScheduleID
#             GROUP BY ds.MealDate, ds.MealType
#             ORDER BY ds.MealDate DESC
#             """
#         )
#         data = cur.fetchall()
#         cur.close()
#         return render_template('ratings.html', data=data, role=session['role'],
#                                member_role=session.get('member_role'))

#     @app.route('/ratings/add', methods=['POST'])
#     def ratings_add():
#         redir = require_login()
#         if redir:
#             return redir

#         if session.get('member_role') not in ('Student', 'Admin'):
#             return jsonify({'error': 'Only students can rate meals'}), 403

#         d   = request.form
#         cur = mysql.connection.cursor()
#         cur.execute(
#             "INSERT INTO MessRating (RatingID, ScheduleID, Rating, RatedOn) "
#             "VALUES (%s, %s, %s, CURDATE())",
#             (d['RatingID'], d['ScheduleID'], d['Rating'])
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Rating {d['Rating']} submitted for schedule {d['ScheduleID']}",
#                    session['username'])
#         return redirect('/ratings')

#     # ─────────────────────────────────────────
#     #  ALL TABLES PAGE (Admin sidebar)
#     # ─────────────────────────────────────────
#     @app.route('/all_tables')
#     def all_tables_page():
#         redir = require_login()
#         if redir:
#             return redir
#         err = require_admin()
#         if err:
#             return err
#         return render_template('all_tables.html',
#                                role=session['role'],
#                                member_role=session.get('member_role'))

#     # ─────────────────────────────────────────
#     #  GENERIC ADMIN CRUD
#     # ─────────────────────────────────────────
#     @app.route('/tables')
#     def get_tables():
#         err = require_admin()
#         if err:
#             return err
#         cur = mysql.connection.cursor()
#         cur.execute("SHOW TABLES")
#         tables = [r[0] for r in cur.fetchall()]
#         cur.close()
#         return jsonify(tables)

#     @app.route('/table/<table_name>')
#     def get_table_data(table_name):
#         err = require_admin()
#         if err:
#             return err
#         cur = mysql.connection.cursor()
#         cur.execute("SHOW TABLES")
#         valid = [r[0] for r in cur.fetchall()]
#         if table_name not in valid:
#             return jsonify({'error': 'Invalid table'}), 400
#         cur.execute("SELECT * FROM `{}`".format(table_name))
#         data    = cur.fetchall()
#         columns = [d[0] for d in cur.description]
#         cur.close()
#         return jsonify({'columns': columns, 'data': data})

#     @app.route('/delete/<table_name>', methods=['POST'])
#     def delete_row(table_name):
#         err = require_admin()
#         if err:
#             return err
#         cur = mysql.connection.cursor()
#         cur.execute("SHOW TABLES")
#         valid = [r[0] for r in cur.fetchall()]
#         if table_name not in valid:
#             return jsonify({'error': 'Invalid table'}), 400
#         d = request.json
#         cur.execute(
#             "DELETE FROM `{}` WHERE `{}` = %s".format(table_name, d['column']),
#             (d['value'],)
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Deleted from {table_name}", session['username'])
#         return jsonify({'message': 'Deleted successfully'})

#     @app.route('/update/<table_name>', methods=['POST'])
#     def update_row(table_name):
#         err = require_admin()
#         if err:
#             return err
#         cur = mysql.connection.cursor()
#         cur.execute("SHOW TABLES")
#         valid = [r[0] for r in cur.fetchall()]
#         if table_name not in valid:
#             return jsonify({'error': 'Invalid table'}), 400
#         d          = request.json
#         pk         = d['columns'][0]
#         pk_val     = d['values'][0]
#         set_clause = ", ".join(["`{}` = %s".format(c) for c in d['columns'][1:]])
#         cur.execute(
#             "UPDATE `{}` SET {} WHERE `{}` = %s".format(table_name, set_clause, pk),
#             d['values'][1:] + [pk_val]
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Updated row in {table_name}", session['username'])
#         return jsonify({'message': 'Updated successfully'})

#     @app.route('/insert/<table_name>', methods=['POST'])
#     def insert_row(table_name):
#         err = require_admin()
#         if err:
#             return err
#         cur = mysql.connection.cursor()
#         cur.execute("SHOW TABLES")
#         valid = [r[0] for r in cur.fetchall()]
#         if table_name not in valid:
#             return jsonify({'error': 'Invalid table'}), 400
#         d    = request.json
#         cols = ", ".join(["`{}`".format(c) for c in d['columns']])
#         ph   = ", ".join(["%s"] * len(d['values']))
#         cur.execute(
#             "INSERT INTO `{}` ({}) VALUES ({})".format(table_name, cols, ph),
#             d['values']
#         )
#         mysql.connection.commit()
#         cur.close()
#         log_action(f"Inserted into {table_name}", session['username'])
#         return jsonify({'message': 'Inserted successfully'})

#     # ─────────────────────────────────────────
#     #  LOGS (admin only)
#     # ─────────────────────────────────────────
#     @app.route('/logs')
#     def get_logs():
#         err = require_admin()
#         if err:
#             return err
#         try:
#             with open('logs/audit.log', 'r') as f:
#                 lines = f.readlines()
#             return jsonify({'logs': [l.strip() for l in lines[-100:]]})
#         except FileNotFoundError:
#             return jsonify({'logs': []})

from flask import request, jsonify, session, render_template, redirect
from db import mysql
from auth import login_user, generate_token, decode_token
from rbac import is_admin, is_student, is_staff
from logging_utils import log_action


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def require_login():
    """For HTML routes — checks Flask session."""
    if 'username' not in session:
        return redirect('/login')
    return None


def require_admin():
    """For JSON/API routes — checks Flask session role."""
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    return None


def get_token_from_request():
    """Extract JWT from Authorization: Bearer <token> header."""
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth.split(' ', 1)[1]
    return None


def validate_token():
    """Decode + validate JWT from request header. Returns payload or None."""
    token = get_token_from_request()
    if not token:
        return None
    return decode_token(token)


# ─────────────────────────────────────────────
#  Route registration
# ─────────────────────────────────────────────
def register_routes(app):

    # ── Home ──────────────────────────────────
    @app.route('/')
    def home():
        return redirect('/login')

    # ── LOGIN ─────────────────────────────────
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Support both HTML form and JSON API calls
            if request.is_json:
                data     = request.get_json()
                username = data.get('user') or data.get('username', '')
                password = data.get('password', '')
            else:
                username = request.form['username']
                password = request.form['password']

            user = login_user(username, password)

            if user:
                # ── Set Flask session (for HTML UI) ────────
                session['username']    = username
                session['role']        = user['role']
                session['member_id']   = user['member_id']
                session['member_role'] = user['member_role']
                session['sub_id']      = user['sub_id']

                # ── Generate JWT token (for API clients) ───
                token, expiry = generate_token(username, user)
                session['jwt_token'] = token   # store so UI can read it too

                log_action('Login', username)

                # JSON request → return token in response
                if request.is_json:
                    return jsonify({
                        'message':       'Login successful',
                        'session token': token,
                        'role':          user['role'],
                        'member_role':   user['member_role'],
                        'expiry':        expiry.isoformat()
                    }), 200

                # HTML form → redirect to dashboard as before
                return redirect('/dashboard')

            else:
                if request.is_json:
                    return jsonify({'error': 'Invalid credentials'}), 401
                return render_template('login.html', error='Invalid credentials')

        # Missing fields check for JSON
        if request.is_json:
            return jsonify({'error': 'Missing parameters'}), 401

        return render_template('login.html', error=None)

    # ── isAuth ────────────────────────────────
    @app.route('/isAuth', methods=['GET'])
    def is_auth():
        """
        Validate a JWT session token.
        Pass token as:  Authorization: Bearer <token>
        OR rely on Flask session (for browser clients).
        """
        # Try JWT token from header first
        payload = validate_token()

        if payload:
            return jsonify({
                'message':  'User is authenticated',
                'username': payload['username'],
                'role':     payload['role'],
                'expiry':   payload['exp']
            }), 200

        # Fall back to Flask session (browser UI)
        if 'username' in session:
            from datetime import datetime, timezone
            return jsonify({
                'message':  'User is authenticated',
                'username': session['username'],
                'role':     session['role'],
                'expiry':   'session-based (no expiry)'
            }), 200

        # Neither valid
        token = get_token_from_request()
        if token is None:
            return jsonify({'error': 'No session found'}), 401

        # Token was present but invalid/expired
        from auth import decode_token as _dt
        import jwt as _jwt
        try:
            _jwt.decode(token, options={"verify_signature": False})
            return jsonify({'error': 'Session expired'}), 401
        except Exception:
            return jsonify({'error': 'Invalid session token'}), 401

    # ── LOGOUT ────────────────────────────────
    @app.route('/logout')
    def logout():
        log_action('Logout', session.get('username', 'unknown'))
        session.clear()
        return redirect('/login')

    # ── SIGNUP ────────────────────────────────
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            d = request.form
            cur = mysql.connection.cursor()

            try:
                # ── 1. Derive username from email ──────────
                username = d['email'].split('@')[0]

                # ── 2. Check for duplicate username / email ─
                cur.execute("SELECT COUNT(*) FROM Users WHERE username=%s", (username,))
                if cur.fetchone()[0] > 0:
                    return render_template('signup.html',
                                           error='Username already exists. Use a different email.')

                cur.execute("SELECT COUNT(*) FROM Member WHERE Email=%s", (d['email'],))
                if cur.fetchone()[0] > 0:
                    return render_template('signup.html',
                                           error='Email already registered.')

                # ── 3. Get next MemberID ───────────────────
                cur.execute("SELECT COALESCE(MAX(MemberID), 0) + 1 FROM Member")
                member_id = cur.fetchone()[0]

                # ── 4. Insert into Member ──────────────────
                cur.execute(
                    "INSERT INTO Member (MemberID, Name, DOB, Email, ContactNumber, Role) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (member_id, d['name'], d['dob'], d['email'],
                     d['contact'], d['member_role'])
                )

                # ── 5. Insert into Student or Staff ────────
                if d['member_role'] == 'Student':
                    cur.execute("SELECT COALESCE(MAX(StudentID), 23110000) + 1 FROM Student")
                    student_id = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO Student (StudentID, MemberID, HostelBlock, RoomNo, Program) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (student_id, member_id,
                         d['hostel_block'], d['room_no'], d['program'])
                    )

                elif d['member_role'] == 'Staff':
                    cur.execute("SELECT COALESCE(MAX(StaffID), 200) + 1 FROM Staff")
                    staff_id = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO Staff (StaffID, MemberID, JobRole, Salary, HireDate) "
                        "VALUES (%s, %s, %s, %s, CURDATE())",
                        (staff_id, member_id, d['job_role'], d['salary'])
                    )

                # ── 6. Insert into Users ───────────────────
                cur.execute(
                    "INSERT INTO Users (username, password, role) VALUES (%s, %s, 'User')",
                    (username, d['password'])
                )

                mysql.connection.commit()
                log_action(f"New signup: {username} ({d['member_role']})", username)
                return render_template('login.html',
                                       error=None,
                                       success=f"Account created! Your username is '{username}'. Please log in.")

            except Exception as e:
                mysql.connection.rollback()
                return render_template('signup.html',
                                       error=f"Signup failed: {str(e)}")
            finally:
                cur.close()

        return render_template('signup.html', error=None)

    # ─────────────────────────────────────────
    #  DASHBOARD  (role-aware landing page)
    # ─────────────────────────────────────────
    @app.route('/dashboard')
    def dashboard():
        redir = require_login()
        if redir:
            return redir

        role        = session.get('role')
        member_role = session.get('member_role')   # 'Admin' | 'Student' | 'Staff'
        member_id   = session.get('member_id')
        cur         = mysql.connection.cursor()

        # ── Admin dashboard ──
        if is_admin(role):
            cur.execute("SELECT COUNT(*) FROM Member")
            total_members = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM Student")
            total_students = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM Staff")
            total_staff = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM MonthlyMessPayment WHERE Status='Pending'")
            pending_bills = cur.fetchone()[0]

            cur.execute("SELECT COALESCE(SUM(TotalCost),0) FROM Purchase")
            total_expense = cur.fetchone()[0]

            cur.execute(
                "SELECT Name, StockQty, Unit, MinStockLevel "
                "FROM Inventory WHERE StockQty <= ReorderLevel"
            )
            low_stock = cur.fetchall()

            cur.close()
            return render_template(
                'dashboard_admin.html',
                role=role, member_role=member_role,
                total_members=total_members,
                total_students=total_students,
                total_staff=total_staff,
                pending_bills=pending_bills,
                total_expense=total_expense,
                low_stock=low_stock
            )

        # ── Student dashboard ──
        elif is_student(member_role):
            cur.execute(
                """
                SELECT m.Name, m.DOB, m.Email, m.ContactNumber,
                       s.HostelBlock, s.RoomNo, s.Program, s.StudentID
                FROM Member m
                JOIN Student s ON m.MemberID = s.MemberID
                WHERE m.MemberID = %s
                """,
                (member_id,)
            )
            profile = cur.fetchone()

            cur.execute(
                """
                SELECT StartDate, EndDate, Amount, Status
                FROM MonthlyMessPayment
                WHERE MemberID = %s
                ORDER BY StartDate DESC LIMIT 6
                """,
                (member_id,)
            )
            payments = cur.fetchall()

            cur.execute(
                """
                SELECT ds.MealDate, ds.MealType, ml.Status
                FROM MealLog ml
                JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
                WHERE ml.MemberID = %s
                ORDER BY ds.MealDate DESC LIMIT 10
                """,
                (member_id,)
            )
            meal_logs = cur.fetchall()

            cur.close()
            return render_template(
                'dashboard_student.html',
                role=role, member_role=member_role,
                profile=profile,
                payments=payments,
                meal_logs=meal_logs
            )

        # ── Staff dashboard ──
        elif is_staff(member_role):
            cur.execute(
                """
                SELECT m.Name, m.DOB, m.Email, m.ContactNumber,
                       st.JobRole, st.Salary, st.HireDate, st.StaffID
                FROM Member m
                JOIN Staff st ON m.MemberID = st.MemberID
                WHERE m.MemberID = %s
                """,
                (member_id,)
            )
            profile = cur.fetchone()

            cur.execute(
                """
                SELECT ShiftDate, ShiftType, CheckInTime, CheckOutTime, TotalHours
                FROM StaffShiftLog
                WHERE StaffID = (SELECT StaffID FROM Staff WHERE MemberID = %s)
                ORDER BY ShiftDate DESC LIMIT 10
                """,
                (member_id,)
            )
            shifts = cur.fetchall()

            cur.close()
            return render_template(
                'dashboard_staff.html',
                role=role, member_role=member_role,
                profile=profile,
                shifts=shifts
            )

        cur.close()
        return "Unknown role", 400

    # ─────────────────────────────────────────
    #  MEMBERS
    # ─────────────────────────────────────────
    @app.route('/members')
    def view_members():
        redir = require_login()
        if redir:
            return redir

        cur = mysql.connection.cursor()
        if is_admin(session.get('role')):
            cur.execute("SELECT * FROM Member ORDER BY MemberID")
        else:
            cur.execute(
                "SELECT * FROM Member WHERE MemberID = %s",
                (session.get('member_id'),)
            )
        members = cur.fetchall()
        cur.close()
        return render_template('members.html', members=members,
                               role=session['role'],
                               member_role=session.get('member_role'))

    # ─────────────────────────────────────────
    #  FUNCTIONALITY 1 — Meal Attendance
    # ─────────────────────────────────────────
    @app.route('/meal_attendance')
    def meal_attendance():
        redir = require_login()
        if redir:
            return redir

        cur = mysql.connection.cursor()

        if is_admin(session.get('role')):
            cur.execute(
                """
                SELECT ds.MealDate, ds.MealType, ml.Status, COUNT(*) AS Total
                FROM MealLog ml
                JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
                GROUP BY ds.MealDate, ds.MealType, ml.Status
                ORDER BY ds.MealDate DESC,
                         FIELD(ds.MealType,'Breakfast','Lunch','Snacks','Dinner')
                """
            )
            data = cur.fetchall()
            cur.close()
            return render_template('meal_attendance.html', data=data,
                                   role=session['role'], view='admin')
        else:
            cur.execute(
                """
                SELECT ds.MealDate, ds.MealType, ml.Status
                FROM MealLog ml
                JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
                WHERE ml.MemberID = %s
                ORDER BY ds.MealDate DESC
                """,
                (session.get('member_id'),)
            )
            data = cur.fetchall()
            cur.close()
            return render_template('meal_attendance.html', data=data,
                                   role=session['role'], view='student')

    # ─────────────────────────────────────────
    #  FUNCTIONALITY 2 — Menu Planning
    # ─────────────────────────────────────────
    @app.route('/menu')
    def menu():
        redir = require_login()
        if redir:
            return redir

        date = request.args.get('date', '')
        cur  = mysql.connection.cursor()

        if date:
            cur.execute(
                """
                SELECT ds.MealDate, ds.MealType, mi.Name, mi.Category,
                       si.QuantityPrepared, si.Unit
                FROM DailySchedule ds
                JOIN Schedule_Items si ON ds.ScheduleID = si.ScheduleID
                JOIN MenuItem mi       ON si.ItemID     = mi.ItemID
                WHERE ds.MealDate = %s
                ORDER BY FIELD(ds.MealType,'Breakfast','Lunch','Snacks','Dinner')
                """,
                (date,)
            )
        else:
            cur.execute(
                """
                SELECT ds.MealDate, ds.MealType, mi.Name, mi.Category,
                       si.QuantityPrepared, si.Unit
                FROM DailySchedule ds
                JOIN Schedule_Items si ON ds.ScheduleID = si.ScheduleID
                JOIN MenuItem mi       ON si.ItemID     = mi.ItemID
                ORDER BY ds.MealDate DESC,
                         FIELD(ds.MealType,'Breakfast','Lunch','Snacks','Dinner')
                LIMIT 40
                """
            )

        data = cur.fetchall()
        cur.close()
        return render_template('menu.html', data=data, role=session['role'],
                               member_role=session.get('member_role'),
                               selected_date=date)

    @app.route('/menu/add', methods=['POST'])
    def menu_add():
        err = require_admin()
        if err:
            return err

        d   = request.form
        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT ScheduleID FROM DailySchedule WHERE MealDate=%s AND MealType=%s",
            (d['MealDate'], d['MealType'])
        )
        row = cur.fetchone()
        if row:
            schedule_id = row[0]
        else:
            cur.execute(
                "INSERT INTO DailySchedule (ScheduleID, MealDate, MealType, IsActive) "
                "VALUES (%s, %s, %s, TRUE)",
                (d['ScheduleID'], d['MealDate'], d['MealType'])
            )
            schedule_id = d['ScheduleID']

        cur.execute(
            "INSERT INTO Schedule_Items (ScheduleID, ItemID, QuantityPrepared, Unit) "
            "VALUES (%s, %s, %s, %s)",
            (schedule_id, d['ItemID'], d['QuantityPrepared'], d['Unit'])
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Menu item {d['ItemID']} added to schedule {schedule_id}", session['username'])
        return redirect('/menu')

    # ─────────────────────────────────────────
    #  FUNCTIONALITY 3 — Monthly Billing
    # ─────────────────────────────────────────
    @app.route('/billing')
    def billing():
        redir = require_login()
        if redir:
            return redir

        cur = mysql.connection.cursor()

        if is_admin(session.get('role')):
            cur.execute(
                """
                SELECT m.Name, mp.StartDate, mp.EndDate, mp.Amount,
                       mp.Status, mp.MonthlyPaymentID
                FROM MonthlyMessPayment mp
                JOIN Member m ON mp.MemberID = m.MemberID
                ORDER BY mp.Status DESC, mp.StartDate DESC
                """
            )
            data = cur.fetchall()
            cur.close()
            return render_template('billing.html', data=data,
                                   role=session['role'], view='admin')
        else:
            cur.execute(
                """
                SELECT StartDate, EndDate, Amount, Status
                FROM MonthlyMessPayment
                WHERE MemberID = %s
                ORDER BY StartDate DESC
                """,
                (session.get('member_id'),)
            )
            data = cur.fetchall()
            cur.close()
            return render_template('billing.html', data=data,
                                   role=session['role'], view='student')

    @app.route('/billing/update_status', methods=['POST'])
    def billing_update_status():
        err = require_admin()
        if err:
            return err

        pid    = request.form['payment_id']
        status = request.form['status']
        cur    = mysql.connection.cursor()
        cur.execute(
            "UPDATE MonthlyMessPayment SET Status=%s WHERE MonthlyPaymentID=%s",
            (status, pid)
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Billing status updated: payment {pid} -> {status}", session['username'])
        return redirect('/billing')

    # ─────────────────────────────────────────
    #  FUNCTIONALITY 4 — Inventory
    # ─────────────────────────────────────────
    @app.route('/inventory')
    def inventory():
        redir = require_login()
        if redir:
            return redir

        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT IngredientID, Name, StockQty, Unit,
                   MinStockLevel, ReorderLevel, LastUpdated,
                   CASE
                       WHEN StockQty <= MinStockLevel THEN 'Critical'
                       WHEN StockQty <= ReorderLevel  THEN 'Low'
                       ELSE 'OK'
                   END AS StockStatus
            FROM Inventory
            ORDER BY StockQty ASC
            """
        )
        data = cur.fetchall()
        cur.close()
        return render_template('inventory.html', data=data, role=session['role'],
                               member_role=session.get('member_role'))

    @app.route('/inventory/update', methods=['POST'])
    def inventory_update():
        err = require_admin()
        if err:
            return err

        d   = request.form
        cur = mysql.connection.cursor()
        cur.execute(
            """
            UPDATE Inventory
            SET StockQty=%s, MinStockLevel=%s, ReorderLevel=%s, LastUpdated=CURDATE()
            WHERE IngredientID=%s
            """,
            (d['StockQty'], d['MinStockLevel'], d['ReorderLevel'], d['IngredientID'])
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Inventory updated: ingredient {d['IngredientID']}", session['username'])
        return redirect('/inventory')

    # ─────────────────────────────────────────
    #  FUNCTIONALITY 5 — Suppliers & Expenses
    # ─────────────────────────────────────────
    @app.route('/suppliers')
    def suppliers():
        redir = require_login()
        if redir:
            return redir

        err = require_admin()
        if err:
            return err

        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT s.SupplierID, s.CompanyName, s.ContactName, s.Phone,
                   s.SupplierType, COALESCE(SUM(p.TotalCost), 0) AS TotalSpent
            FROM Supplier s
            LEFT JOIN Purchase p ON s.SupplierID = p.SupplierID
            GROUP BY s.SupplierID
            ORDER BY TotalSpent DESC
            """
        )
        suppliers_data = cur.fetchall()

        cur.execute(
            """
            SELECT p.PurchaseID, s.CompanyName, i.Name AS Ingredient,
                   p.Quantity, p.UnitPrice, p.TotalCost, p.PurchaseDate
            FROM Purchase p
            JOIN Supplier s  ON p.SupplierID   = s.SupplierID
            JOIN Inventory i ON p.IngredientID = i.IngredientID
            ORDER BY p.PurchaseDate DESC
            LIMIT 20
            """
        )
        purchases = cur.fetchall()
        cur.close()

        return render_template('suppliers.html', suppliers=suppliers_data,
                               purchases=purchases, role=session['role'])

    # ─────────────────────────────────────────
    #  FUNCTIONALITY 6 — Food Waste
    # ─────────────────────────────────────────
    @app.route('/waste')
    def waste():
        redir = require_login()
        if redir:
            return redir

        err = require_admin()
        if err:
            return err

        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT ds.MealDate, ds.MealType,
                   w.WasteQty_Kg, w.Waste_category, w.RecordedDate
            FROM WasteLog w
            JOIN DailySchedule ds ON w.ScheduleID = ds.ScheduleID
            ORDER BY w.RecordedDate DESC
            """
        )
        data = cur.fetchall()

        cur.execute(
            """
            SELECT Waste_category, SUM(WasteQty_Kg) AS Total
            FROM WasteLog
            GROUP BY Waste_category
            """
        )
        totals = cur.fetchall()
        cur.close()

        return render_template('waste.html', data=data, totals=totals,
                               role=session['role'])

    @app.route('/waste/add', methods=['POST'])
    def waste_add():
        err = require_admin()
        if err:
            return err

        d   = request.form
        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO WasteLog (WasteID, ScheduleID, WasteQty_Kg, Waste_category, RecordedDate)
            VALUES (%s, %s, %s, %s, CURDATE())
            """,
            (d['WasteID'], d['ScheduleID'], d['WasteQty_Kg'], d['Waste_category'])
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Waste logged for schedule {d['ScheduleID']}", session['username'])
        return redirect('/waste')

    # ─────────────────────────────────────────
    #  FUNCTIONALITY 7 — Meal Ratings
    # ─────────────────────────────────────────
    @app.route('/ratings')
    def ratings():
        redir = require_login()
        if redir:
            return redir

        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT ds.MealDate, ds.MealType,
                   ROUND(AVG(mr.Rating), 2) AS AvgRating,
                   COUNT(mr.RatingID)       AS TotalRatings,
                   MIN(mr.Rating)           AS MinRating,
                   MAX(mr.Rating)           AS MaxRating
            FROM MessRating mr
            JOIN DailySchedule ds ON mr.ScheduleID = ds.ScheduleID
            GROUP BY ds.MealDate, ds.MealType
            ORDER BY ds.MealDate DESC
            """
        )
        data = cur.fetchall()
        cur.close()
        return render_template('ratings.html', data=data, role=session['role'],
                               member_role=session.get('member_role'))

    @app.route('/ratings/add', methods=['POST'])
    def ratings_add():
        redir = require_login()
        if redir:
            return redir

        if session.get('member_role') not in ('Student', 'Admin'):
            return jsonify({'error': 'Only students can rate meals'}), 403

        d   = request.form
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO MessRating (RatingID, ScheduleID, Rating, RatedOn) "
            "VALUES (%s, %s, %s, CURDATE())",
            (d['RatingID'], d['ScheduleID'], d['Rating'])
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Rating {d['Rating']} submitted for schedule {d['ScheduleID']}",
                   session['username'])
        return redirect('/ratings')

    # ─────────────────────────────────────────
    #  ALL TABLES PAGE (Admin sidebar)
    # ─────────────────────────────────────────
    @app.route('/all_tables')
    def all_tables_page():
        redir = require_login()
        if redir:
            return redir
        err = require_admin()
        if err:
            return err
        return render_template('all_tables.html',
                               role=session['role'],
                               member_role=session.get('member_role'))

    # ─────────────────────────────────────────
    #  GENERIC ADMIN CRUD
    # ─────────────────────────────────────────
    @app.route('/tables')
    def get_tables():
        err = require_admin()
        if err:
            return err
        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        tables = [r[0] for r in cur.fetchall()]
        cur.close()
        return jsonify(tables)

    @app.route('/table/<table_name>')
    def get_table_data(table_name):
        err = require_admin()
        if err:
            return err
        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        valid = [r[0] for r in cur.fetchall()]
        if table_name not in valid:
            return jsonify({'error': 'Invalid table'}), 400
        cur.execute("SELECT * FROM `{}`".format(table_name))
        data    = cur.fetchall()
        columns = [d[0] for d in cur.description]
        cur.close()
        return jsonify({'columns': columns, 'data': data})

    @app.route('/delete/<table_name>', methods=['POST'])
    def delete_row(table_name):
        err = require_admin()
        if err:
            return err
        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        valid = [r[0] for r in cur.fetchall()]
        if table_name not in valid:
            return jsonify({'error': 'Invalid table'}), 400
        d = request.json
        cur.execute(
            "DELETE FROM `{}` WHERE `{}` = %s".format(table_name, d['column']),
            (d['value'],)
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Deleted from {table_name}", session['username'])
        return jsonify({'message': 'Deleted successfully'})

    @app.route('/update/<table_name>', methods=['POST'])
    def update_row(table_name):
        err = require_admin()
        if err:
            return err
        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        valid = [r[0] for r in cur.fetchall()]
        if table_name not in valid:
            return jsonify({'error': 'Invalid table'}), 400
        d          = request.json
        pk         = d['columns'][0]
        pk_val     = d['values'][0]
        set_clause = ", ".join(["`{}` = %s".format(c) for c in d['columns'][1:]])
        cur.execute(
            "UPDATE `{}` SET {} WHERE `{}` = %s".format(table_name, set_clause, pk),
            d['values'][1:] + [pk_val]
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Updated row in {table_name}", session['username'])
        return jsonify({'message': 'Updated successfully'})

    @app.route('/insert/<table_name>', methods=['POST'])
    def insert_row(table_name):
        err = require_admin()
        if err:
            return err
        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        valid = [r[0] for r in cur.fetchall()]
        if table_name not in valid:
            return jsonify({'error': 'Invalid table'}), 400
        d    = request.json
        cols = ", ".join(["`{}`".format(c) for c in d['columns']])
        ph   = ", ".join(["%s"] * len(d['values']))
        cur.execute(
            "INSERT INTO `{}` ({}) VALUES ({})".format(table_name, cols, ph),
            d['values']
        )
        mysql.connection.commit()
        cur.close()
        log_action(f"Inserted into {table_name}", session['username'])
        return jsonify({'message': 'Inserted successfully'})

    # ─────────────────────────────────────────
    #  LOGS (admin only)
    # ─────────────────────────────────────────
    @app.route('/logs')
    def get_logs():
        err = require_admin()
        if err:
            return err
        try:
            with open('logs/audit.log', 'r') as f:
                lines = f.readlines()
            return jsonify({'logs': [l.strip() for l in lines[-100:]]})
        except FileNotFoundError:
            return jsonify({'logs': []})