"""
Vision system configuration.
Camera list defined once here — everything else flows from this.
"""

CON_VISION = {
    "cameras": {
        "shooter": {
            "name": "Limelight Shooter",
            "host": "10.97.71.11",
        },
        "front": {
            "name": "Limelight Front",
            "host": "limelight-front",  # TODO: set static IP when connected
        },
    },
}
