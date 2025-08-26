import uuid

def unique_slug_generator(instance):
    return str(uuid.uuid4())[:8]