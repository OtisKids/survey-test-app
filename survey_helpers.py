import uuid

def compute_average_rating(survey):
    """
    Compute the average rating for a survey.
    If there are no ratings, default to 4.
    """
    ratings = survey.get("ratings", [])
    return round(sum(ratings) / len(ratings), 2) if ratings else 4

def generate_unique_id():
    """
    Generate a unique identifier for a survey instance.
    """
    return str(uuid.uuid4())
