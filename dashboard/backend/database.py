from supabase import create_client, Client
from config import get_settings
from auth import hash_password, verify_password

settings = get_settings()

class SupabaseDB:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def register_user(self, email: str, password: str, full_name: str = None):
        """Register a new user"""
        hashed_pwd = hash_password(password)
        
        try:
            response = self.client.table("users").insert({
                "email": email,
                "password_hash": hashed_pwd,
                "full_name": full_name,
                "role": "user"
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Registration failed: {str(e)}")
    
    async def get_user_by_email(self, email: str):
        """Get user by email"""
        response = self.client.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    
    async def verify_user_password(self, email: str, password: str):
        """Verify user credentials"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if verify_password(password, user.get("password_hash")):
            return user
        return None
    
    async def get_dashboard_metrics(self, user_id: str):
        """Get dashboard metrics for user"""
        response = self.client.table("dashboard_metrics").select("*").eq("user_id", user_id).execute()
        return response.data if response.data else []

db = SupabaseDB()