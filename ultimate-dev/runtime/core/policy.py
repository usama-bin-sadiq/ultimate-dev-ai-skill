DESTRUCTIVE = {
    "delete_data","drop_database","force_push","destroy_infrastructure",
    "rotate_credentials","publish_release","production_deploy"
}
class Policy:
    def __init__(self, confirmation_required=None):
        self.confirmation_required = set(confirmation_required or DESTRUCTIVE)
    def check(self, action: str, confirmed: bool=False) -> dict:
        required = action in self.confirmation_required
        return {"allowed": (not required) or confirmed, "confirmation_required": required}
