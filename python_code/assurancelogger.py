#    Copyright (C) <2025>  <Johannes Löbbecke>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

class AssuranceLogger(logging.Logger):
    """
    Custom logger that reduces an assurance level when warnings are logged
    and stores the Activities and missing Activities such that the Compliance Log
    is a bit more useful. Shared states are achieved using class-level attributes.
    """
    # Class-level shared state
    assurance_level = 100  # Shared assurance level
    activities = set()  # Shared activities set
    missing_activities = set()  # Shared missing activities set
    instance_Id = None 


    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

    def warning(self, msg, *args, **kwargs):
        """
        Override the `warning` method to reduce the assurance level
        whenever a warning is logged.
        """
        type(self).assurance_level -= 10  # Decrease assurance level
        type(self).assurance_level = max(0, type(self).assurance_level)  # Ensure it doesn't go below 0
        super().warning(msg, *args, **kwargs)  # Call the original `warning` method

    @classmethod
    def get_id(cls):
        return cls.instance_Id

    @classmethod
    def set_id(cls, Id):
        cls.instance_Id = Id

    @classmethod
    def get_assurance_level(cls):
        """
        Retrieve the current assurance level.
        """
        return cls.assurance_level

    @classmethod
    def add_activity(cls, activity):
        """Add an activity to the shared set."""
        cls.activities.add(activity)

    @classmethod
    def reset_activities(cls):
        """Reset the activities set."""
        cls.activities = set()

    @classmethod
    def get_activities(cls):
        """Retrieve the current activities set."""
        return cls.activities

    @classmethod
    def add_missing_activity(cls, activity):
        """Add a missing activity to the shared set."""
        cls.missing_activities.add(activity)

    @classmethod
    def reset_missing_activities(cls):
        """Reset the missing activities set."""
        cls.missing_activities = set()

    @classmethod
    def get_missing_activities(cls):
        """Retrieve the current missing activities set."""
        return cls.missing_activities

    @classmethod
    def reset_assurance_level(cls):
        """
        Reset the assurance level to 100.
        """
        cls.assurance_level = 100


# Set AssuranceLogger as the default logger class globally
logging.setLoggerClass(AssuranceLogger)

