"""Bronze Layer SQLModel definitions using framework BronzeMetadata"""

from .actor import ActorBronze
from .address import AddressBronze
from .category import CategoryBronze
from .city import CityBronze
from .country import CountryBronze
from .customer import CustomerBronze
from .film import FilmBronze
from .film_actor import FilmActorBronze
from .film_category import FilmCategoryBronze
from .inventory import InventoryBronze
from .language import LanguageBronze
from .payment import PaymentBronze
from .rental import RentalBronze
from .staff import StaffBronze
from .store import StoreBronze

__all__ = [
    "ActorBronze",
    "AddressBronze",
    "CategoryBronze",
    "CityBronze",
    "CountryBronze",
    "CustomerBronze",
    "FilmBronze",
    "FilmActorBronze",
    "FilmCategoryBronze",
    "InventoryBronze",
    "LanguageBronze",
    "PaymentBronze",
    "RentalBronze",
    "StaffBronze",
    "StoreBronze",
]