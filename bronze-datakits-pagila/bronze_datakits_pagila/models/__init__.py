"""Bronze Layer SQLModel definitions using framework BronzeMetadata"""

from .film import FilmBronze
from .actor import ActorBronze
from .customer import CustomerBronze

__all__ = ["FilmBronze", "ActorBronze", "CustomerBronze"]