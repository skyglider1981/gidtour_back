from app.models.user import User, BusinessProfile, CustomerProfile
from app.models.activity import ActivityType, Location, Activity, LocationActivity
from app.models.resource import ResourceType, Resource, Instructor, ScheduleResource, ActivityResourceType
from app.models.tour import Tour, TourActivity, TourResource, TourInstructor, TourLocation, TourSchedule
from app.models.schedule import ScheduleTemplate, ResourceAllocation
from app.models.booking import Booking, BookingResource

# === НОВОЕ: Модели отзывов ===
from app.models.review import Review, ReviewVote, TourRatingStats
