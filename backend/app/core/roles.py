from app.models import User


def get_role_names(user: User) -> list[str]:
    return [role.name for role in user.roles]


def is_cod(user: User) -> bool:
    return "COD" in get_role_names(user)


def is_sales_manager(user: User) -> bool:
    return "Sales Manager" in get_role_names(user)


def is_sales_specialist(user: User) -> bool:
    return "Sales Specialist" in get_role_names(user)


def is_procurement_manager(user: User) -> bool:
    return "Procurement Manager" in get_role_names(user)


def is_procurement_specialist(user: User) -> bool:
    return "Procurement Specialist" in get_role_names(user)


def is_logistics_coordinator(user: User) -> bool:
    return "Logistics Coordinator" in get_role_names(user)


def has_procurement_access(user: User) -> bool:
    return is_procurement_manager(user) or is_cod(user)


def has_sales_management_access(user: User) -> bool:
    return is_sales_manager(user) or is_cod(user)


def has_logistics_coordinator_access(user: User) -> bool:
    return is_procurement_manager(user) or is_cod(user)