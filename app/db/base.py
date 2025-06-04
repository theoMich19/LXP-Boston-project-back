# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.candidate import Candidate  # noqa
from app.models.user import User  # noqa
from app.models.cv import CV  # noqa
from app.models.job_offer import JobOffer  # noqa
from app.models.match import Match  # noqa 