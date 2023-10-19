from services.config_loader_service import ConfigLoaderService

configLoaderService = ConfigLoaderService()

class UsersService:

    def get_user(self, user_id: int):
        users_by_id = configLoaderService.load_users_by_id_from_yaml()
        if user_id not in users_by_id:
            raise ValueError(f"The user {str(user_id)} is not present in users configuration")
        return users_by_id[user_id]

    def list_users(self):
        return configLoaderService.load_users_from_yaml()