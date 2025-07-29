def check_screening_to_long(data):
    if data["apartment_type"] in ["в бетоне", "вайт бокс"]:
        return True
    
    if data["measurement_type"] == "archicad":
        return True
    return False

def continuety(data):
    if check_screening_to_long(data):
        return 4
    return 3
