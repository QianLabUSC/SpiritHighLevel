# SpatialMeasurement.msg
# A spatially tied measurement from a sensor.

# The 3D position (xyz) of the measurement point.
geometry_msgs/Point position

# Primary measurement details
float32 value                  # Measurement value
float32 uncertainty            # Measurement uncertainty

# Optional metadata for additional context
string unit                    # Unit of measurement (e.g., "m", "C", etc.)
string source_name             # Name or identifier of the sensor/source

# Measurement time information
builtin_interfaces/Time time            # Single timestamp for the measurement
# OR, for time-interval-based measurements
builtin_interfaces/Time start_time      # Start time of the measurement
builtin_interfaces/Time end_time        # End time of the measurement
