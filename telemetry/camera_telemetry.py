"""
Camera stream registration.
Registers each Limelight MJPEG stream with CameraServer so
Elastic Dashboard can display the video feeds.
"""

from constants import CON_VISION


def setup_camera_streams():
    """Register an HttpCamera for each Limelight defined in CON_VISION."""
    import cscore

    for key, cam in CON_VISION["cameras"].items():
        camera = cscore.HttpCamera(
            cam["name"],
            f"http://{cam['host']}:5800/stream.mjpg",
        )
        cscore.CameraServer.addCamera(camera)
