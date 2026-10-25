from django import template

register = template.Library()


@register.filter
def has_role(user, roles):
    """Return True if user.user_type is in the comma-separated roles list."""
    if not user.is_authenticated:
        return False
    role_list = [role.strip() for role in roles.split(',')]
    return user.user_type in role_list
