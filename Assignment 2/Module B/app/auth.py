# # from db import mysql

# # def login_user(username, password):
# #     cur = mysql.connection.cursor()
# #     cur.execute(
# #         "SELECT role FROM Users WHERE username=%s AND password=%s",
# #         (username, password)
# #     )
# #     user = cur.fetchone()

# #     if user:
# #         return user[0]  # role
# #     return None

# from db import mysql

# def login_user(username, password):
#     cur = mysql.connection.cursor()
#     cur.execute(
#         "SELECT user_id, role FROM Users WHERE username=%s AND password=%s",
#         (username, password)
#     )
#     user = cur.fetchone()
#     if not user:
#         return None

#     user_id, role = user

#     # Admin — no Member record needed
#     if role == 'Admin':
#         return {
#             'role':        'Admin',
#             'member_id':   None,
#             'member_role': 'Admin',   # 'Student' | 'Staff' | 'Admin'
#             'sub_id':      None       # StudentID or StaffID
#         }

#     # Regular user — look up Member via email prefix matching username
#     # e.g. username 'amit' matches Email 'amit@uni.edu'
#     cur.execute(
#         "SELECT MemberID, Role FROM Member "
#         "WHERE SUBSTRING_INDEX(Email, '@', 1) = %s",
#         (username,)
#     )
#     member = cur.fetchone()

#     if not member:
#         return {
#             'role':        role,
#             'member_id':   None,
#             'member_role': 'Unknown',
#             'sub_id':      None
#         }

#     member_id, member_role = member   # member_role = 'Student' or 'Staff'

#     sub_id = None
#     if member_role == 'Student':
#         cur.execute("SELECT StudentID FROM Student WHERE MemberID=%s", (member_id,))
#         row = cur.fetchone()
#         sub_id = row[0] if row else None
#     elif member_role == 'Staff':
#         cur.execute("SELECT StaffID FROM Staff WHERE MemberID=%s", (member_id,))
#         row = cur.fetchone()
#         sub_id = row[0] if row else None

#     return {
#         'role':        role,          # 'User'
#         'member_id':   member_id,
#         'member_role': member_role,   # 'Student' or 'Staff'
#         'sub_id':      sub_id
#     }

import jwt
from datetime import datetime, timedelta, timezone
from db import mysql, JWT_SECRET, JWT_EXPIRY_HOURS


# ─────────────────────────────────────────────
#  Verify credentials → return user dict or None
# ─────────────────────────────────────────────
def login_user(username, password):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT user_id, role FROM Users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cur.fetchone()
    if not user:
        return None

    user_id, role = user

    # Admin — no Member record needed
    if role == 'Admin':
        return {
            'role':        'Admin',
            'member_id':   None,
            'member_role': 'Admin',
            'sub_id':      None
        }

    # Regular user — find Member via email prefix matching username
    cur.execute(
        "SELECT MemberID, Role FROM Member "
        "WHERE SUBSTRING_INDEX(Email, '@', 1) = %s",
        (username,)
    )
    member = cur.fetchone()

    if not member:
        return {
            'role':        role,
            'member_id':   None,
            'member_role': 'Unknown',
            'sub_id':      None
        }

    member_id, member_role = member

    sub_id = None
    if member_role == 'Student':
        cur.execute("SELECT StudentID FROM Student WHERE MemberID=%s", (member_id,))
        row    = cur.fetchone()
        sub_id = row[0] if row else None
    elif member_role == 'Staff':
        cur.execute("SELECT StaffID FROM Staff WHERE MemberID=%s", (member_id,))
        row    = cur.fetchone()
        sub_id = row[0] if row else None

    return {
        'role':        role,          # 'User'
        'member_id':   member_id,
        'member_role': member_role,   # 'Student' or 'Staff'
        'sub_id':      sub_id
    }


# ─────────────────────────────────────────────
#  Generate a JWT token for a logged-in user
# ─────────────────────────────────────────────
def generate_token(username, user_dict):
    """
    Returns a signed JWT string.
    Payload includes username, role, member_role, expiry.
    """
    expiry = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)

    payload = {
        'username':    username,
        'role':        user_dict['role'],
        'member_role': user_dict['member_role'],
        'member_id':   user_dict['member_id'],
        'sub_id':      user_dict['sub_id'],
        'exp':         expiry          # PyJWT reads this automatically for expiry check
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token, expiry


# ─────────────────────────────────────────────
#  Decode and validate a JWT token
# ─────────────────────────────────────────────
def decode_token(token):
    """
    Returns decoded payload dict on success.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None   # token expired
    except jwt.InvalidTokenError:
        return None   # tampered or malformed