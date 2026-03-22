def is_admin(role):
    """Pass session.get('role')"""
    return role == 'Admin'

def is_student(member_role):
    """Pass session.get('member_role')"""
    return member_role == 'Student'

def is_staff(member_role):
    """Pass session.get('member_role')"""
    return member_role == 'Staff'
