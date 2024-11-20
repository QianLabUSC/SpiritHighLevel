# ExtrapolatedMap.msg
# Estimated map from given data (image-like)
# Often produced with Gaussian Process Regression

std_msgs/Header header
nav_msgs/MapMetaData meta
uint32 height                     # Number of rows (height of the 2D data)
uint32 width                      # Number of columns (width of the 2D data)
float32[] data                    # Flattened predicted values (interpretable as height x width)
float32[] uncertainty             # Flattened uncertainty values (interpretable as height x width)
