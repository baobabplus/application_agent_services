from datetime import datetime, timedelta


def get_week_range(offset: int = 0):
    """
    Get the start (Monday) and end (Sunday) dates of a specific week relative to the current week.

    Args:
        offset (int): The number of weeks to offset from the current week.
                      0 = current week, -1 = previous week, 1 = next week, etc.

    Returns:
        tuple: A tuple containing the start (Monday) and end (Sunday) dates of
        the specified week in 'YYYY-MM-DD' format.
    """
    today = datetime.now()
    # Calculate the Monday of the current week
    current_monday = today - timedelta(days=today.weekday())
    # Adjust for the target week
    target_monday = current_monday + timedelta(weeks=offset)
    # Calculate the Sunday of the target week
    target_sunday = target_monday + timedelta(days=6)

    # Format as 'YYYY-MM-DD'
    start_of_week_str = target_monday.strftime("%Y-%m-%d")
    end_of_week_str = target_sunday.strftime("%Y-%m-%d")

    return start_of_week_str, end_of_week_str


print(get_week_range(-1))  # ('2023-11-06', '2023-11-12')
